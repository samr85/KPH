'use strict'
var countdownTarget
var countdownTimeOffset
var countdownString
var countdownInterval

var numFull = String.raw`/¯¯\  /|  /¯¯\ /¯¯\  /|  |¯¯¯ /¯¯\ |¯¯| /¯¯\ /¯¯\      ` +
              String.raw`|  |   |    _/  __/ /_|_ |__  |__     / \__/ \__|   o  ` +
              String.raw`|  |   |   /      \   |     \ |  \   |  /  \    |   o  ` +
              String.raw`\__/   |  /___ \__/   |  ___/ \__/   |  \__/  __/      `;
var numbers = [];
var i;
for (i = 0; i < 11; i++) {
    var nextNum = "<pre class='largenumber'>"
    var j;
    for (j = 0; j < 4; j++) {
        var index = (i + j * 11) * 5;
        nextNum += numFull.substring(index, index + 5) + "\n";
    }
    nextNum += "</pre>";
    nextNum = nextNum.replace(/¯/g, "&macr;");
    numbers.push($(nextNum));
}


function countdownTick() {
    var countdownDiv = $("#countdownTime");
    var msec = countdownTarget - Date.now() - countdownTimeOffset;
    if (msec < 0) {
        msec = 0;
    }
    var hh = Math.floor(msec / 1000 / 60 / 60);
    msec -= hh * 1000 * 60 * 60;
    var mm = Math.floor(msec / 1000 / 60);
    msec -= mm * 1000 * 60;
    var ss = Math.floor(msec / 1000);
    msec -= ss * 1000;
    countdownDiv.empty()
    countdownDiv.append(numbers[Math.floor((hh / 10) % 10)].clone())
    countdownDiv.append(numbers[hh % 10].clone())
    countdownDiv.append(numbers[10].clone())
    countdownDiv.append(numbers[Math.floor((mm / 10) % 10)].clone())
    countdownDiv.append(numbers[mm % 10].clone())
    countdownDiv.append(numbers[10].clone())
    countdownDiv.append(numbers[Math.floor((ss / 10) % 10)].clone())
    countdownDiv.append(numbers[ss % 10].clone())
}

function updateCountdown(id, sortValue, data) {
    if (id == 0) {
        countdownString = data;
    } else if (id == 1) {
        countdownTarget = Date.parse(data);
        countdownTimeOffset = Date.parse(sortValue) - Date.now();
    } else {
        console.log("Invalid id in updateCountdown: %d", id);
        return;
    }
    if (countdownInterval) {
        clearInterval(countdownInterval);
    }
    if (countdownString) {
        var newHTML = "<div>" + countdownString + "</div><div id='countdownTime'></div>";
        $("#countdownDiv").html(newHTML);
        countdownTick();
        setInterval(countdownTick, 500);
    } else {
        $("#countdownDiv").empty();
    }
}

initialiseSection("countdown", updateCountdown, []);
