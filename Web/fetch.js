var fs = require('fs');
var request = require('request');

var log4js = require('log4js');

var logger = confLog(log4js);


/////////////////////////////////////////////////
// MAIN GOES BELOW /////////////////////////////

searchVk(10)
	.then(processSearchData)
	.then(items => { console.log(items) })
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

function searchVk(count) {
	// Method documentation: "https://vk.com/dev/users.search"

	var url = "https://api.vk.com/method/users.search";
	query = {
		"count": count,
		"sex":1,
		"country": 1, // from russia
		"has_photo": 1,
		"fields": "connections"// get links to instagram ,skype...
	};
	var token = loadlocaltoken(); // load API token from filesystem
	query.access_token = token;
	query.v = "5.68"
	return new Promise((resolve, reject) => {
		// Make an http to search api
		request({ url: url, qs: query }, function (err, res, body) {
		//	console.log("Search returned:",body);
			if (err) { reject(err); }
			else {
				// parse response
				var answ = JSON.parse(body);
				if (answ.error == null) {
					// if request succesfull, resolve promice with _items_ of search
					resolve(answ.response.items);
				} else {
					// if Vk api returned an error, reject promice
					reject(answ.error);
				}
			}
		});
	});
}


function confLog(log4js) {
	log4js.clearAppenders();
	log4js.loadAppender('file');
	log4js.addAppender(log4js.appenders.file('.log'), 'serv');
}

function loadlocaltoken() {
	return fs.readFileSync('.vktoken').slice(0, -1).toString();
}