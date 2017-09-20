var fs = require('fs');
var request = require('request');

var log4js = require('log4js');

var logger = confLog(log4js);

var rawdataPath = '../data/rawusers.json';
/////////////////////////////////////////////////
// MAIN GOES BELOW /////////////////////////////

searchVk(1000,200)
	.then(processSearchData)
	.then(getUsersData)
	.then(items => {
		console.log("ITEMS", items.map(a => a.id));
		var file = fs.readFileSync(rawdataPath);
		if(file.length>0){
			try{
				var rawdata = JSON.parse(file).concat(items)
			} catch (err) { console.log("error parsing", err); var rawdata = items }
		}else{ var rawdata = items}
		
		console.log("writing",rawdata.length,"items to file");
		fs.writeFileSync(rawdataPath,JSON.stringify(rawdata));
	})
	.catch(error => { console.log(error) });

// MAIN ENDS ////////////////////////////////////
////////////////////////////////////////////////


// VK Functions //
function processSearchData(data){

	if(data!=undefined){
	return data.map((u) => {
		user = {
			id: u.id,
			name: u.first_name +" "+ u.last_name, // concat the name
		}
		// Add a link to instagram if exists
		if(u.instagram != undefined){
			user["instagram"] = u.instagram;
		}
		return user;
		})
	}
	else {
		return new Error("No search result elements");
	}
}


function getUsersData(users){

	let chain = Promise.resolve();

	var infourl = "https://api.vk.com/method/users.get";
	var photourl = "https://api.vk.com/method/photos.get";
	var groupsurl = "https://api.vk.com/method/photos.users.getSubscriptions";

	var token = loadlocaltoken();

	let result = [];
	// start making chain of requests for each element of users []
	users.forEach(function(user,idx) {
		let userid = user.id;
		chain = chain
			.then(()=>{  // Get info about user (friends count,etc)
				query = {
					"user_ids": userid,
					"fields": "counters,city"
				}	
				// pass query data and once loaded token to request
				return vkRequestMaker(infourl,query,token).then(
					i=>i.response[0],
					(err)=>{console.log(err); return {}; });
			})
			.then((info)=>{ // get links to user's photos
				query={
					"owner_id":userid,
					"count":10,
					"photo_sizes":0,
					"album_id":"profile",
					"extended":1 // will return likes and reposts
				}	
				return vkRequestMaker(photourl,query,token) 
					.then(p=>{  
						// concat data with info
						info["photos"]=p.response.items;
						return info;
					},(err)=>{
						if (!isEmpty(info) ) { // check if previous call suceeded
							return info;
						} else {
							throw new Error(err);
						}
					});
			})
				// concat with user and push results 
			.then(data=>{
				result.push(collectVals(user,data));
				 console.log("finished with ",idx,userid)
				},
				(err)=>{
					console.log("FAILED TO FETCH ", idx, userid, err);
					return new Promise((resolve, reject) => {
						setTimeout(resolve, 1300);
					}).then(() => getUsersData([user]))
						.then((data) => result.push(collectVals(user, data[0])),
							() => console.log("error"));

					//result.push(user);
				}
		)/*.then(() => {
			return new Promise((resolve,reject)=>{
				setTimeout(resolve, 400);
			})}
		)*/
	});

	chain = chain.then(() => {
		if (result.length === 0) {
			throw new Error("Nothing fetched at all");
		}
		return result;
	});
	return chain
}

function searchVk(offset,count) {
	// Method documentation: "https://vk.com/dev/users.search"
	var url = "https://api.vk.com/method/users.search";
	query = {
		"count": count,
		"offset":offset,
		"sex":1,
		"country": 1, // from russia
		"has_photo": 1,
		"fields": "connections"// get links to instagram ,skype...
	};
	return vkRequestMaker(url,query).then(u=>u.response.items);
};

// Function that handles http and loads token to query
function vkRequestMaker(url,query,token){
	if(token==null){
		var token = loadlocaltoken(); // load API token from filesystem
	}
	query["access_token"]=token;
	query.v = "5.68"
	return new Promise((resolve, reject) => {
		// Make an http to search api
		request({ url: url, qs: query }, function (err, res, body) {
			//console.log("req returned:",body," url:",url);
			if (err) { reject(err); }
			else {
				// parse response
				var answ = JSON.parse(body);
				if (answ.error == null) {
					// if request succesfull, resolve promice with _items_ of search
					resolve(answ);
				} else {
					// if Vk api returned an error, reject promice
					reject(answ.error);
				}
			}
		});
	});
}
function collectVals(o1, o2) {
 for (var key in o2) {
  o1[key] = o2[key];
 }
 return o1;
}

function confLog(log4js) {
	log4js.clearAppenders();
	log4js.loadAppender('file');
	log4js.addAppender(log4js.appenders.file('.log'), 'serv');
}

function loadlocaltoken() {
	return fs.readFileSync('.vktoken').slice(0, -1).toString();
}

var hasOwnProperty = Object.prototype.hasOwnProperty;

function isEmpty(obj) {

    // null and undefined are "empty"
    if (obj == null) return true;

    // Assume if it has a length property with a non-zero value
    // that that property is correct.
    if (obj.length > 0)    return false;
    if (obj.length === 0)  return true;

    // If it isn't an object at this point
    // it is empty, but it can't be anything *but* empty
    // Is it empty?  Depends on your application.
    if (typeof obj !== "object") return true;

    // Otherwise, does it have any properties of its own?
    // Note that this doesn't handle
    // toString and valueOf enumeration bugs in IE < 9
    for (var key in obj) {
        if (hasOwnProperty.call(obj, key)) return false;
    }

    return true;
}