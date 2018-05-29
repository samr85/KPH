'use strict';
var countdownTarget; /* Time that we should be counting down to */
var countdownTimeOffset; /* Time difference between this browser and the server */
var countdownString; /* Message to display with the countdown */
var countdownInterval; /* Reference to the interval which countdownTick is called on */

/* Create a numbers array, which is a HTML element containing the ascii art for each number, or colon */
var numFull = String.raw`/¯¯\  /|  /¯¯\ /¯¯\  /|  |¯¯¯ /¯¯\ |¯¯| /¯¯\ /¯¯\      ` +
              String.raw`|  |   |    _/  __/ /_|_ |__  |__     / \__/ \__|   o  ` +
              String.raw`|  |   |   /      \   |     \ |  \   |  /  \    |   o  ` +
              String.raw`\__/   |  /___ \__/   |  ___/ \__/   |  \__/  __/      `;
var numbers = [];
var i;
for (i = 0; i < 11; i++) {
    var nextNum = "<pre class='largenumber'>";
    var j;
    for (j = 0; j < 4; j++) {
        var index = (i + j * 11) * 5;
        nextNum += numFull.substring(index, index + 5) + "\n";
    }
    nextNum += "</pre>";
    /* This character just shows up as a box on webpages, so convert to the entity that it represents so it displays ok */
    nextNum = nextNum.replace(/¯/g, "&macr;");
    numbers.push($(nextNum));
}


function countdownTick() {
    var countdownDiv = $("#countdownTime");
    if (isNaN(countdownTarget)) {
        console.log("No valid countdown timer");
        countdownDiv.empty();
        return;
    }
    var msec = countdownTarget - Date.now() - countdownTimeOffset;
    if (msec < 0) {
        msec = 0;
    }
    var hh = Math.floor(msec / 1000 / 60 / 60);
    if (hh > 99){
        console.log("Error: countdown time longer than 99 hours! %d", hh);
        msec = 0;
        hh = 0;
    }
    msec -= hh * 1000 * 60 * 60;
    var mm = Math.floor(msec / 1000 / 60);
    msec -= mm * 1000 * 60;
    var ss = Math.floor(msec / 1000);
    msec -= ss * 1000;
    countdownDiv.empty();
    try {
        countdownDiv.append(numbers[Math.floor((hh / 10) % 10)].clone());
        countdownDiv.append(numbers[hh % 10].clone());
        countdownDiv.append(numbers[10].clone());
        countdownDiv.append(numbers[Math.floor((mm / 10) % 10)].clone());
        countdownDiv.append(numbers[mm % 10].clone());
        countdownDiv.append(numbers[10].clone());
        countdownDiv.append(numbers[Math.floor((ss / 10) % 10)].clone());
        countdownDiv.append(numbers[ss % 10].clone());
    }
    catch (error) {
        console.log("Failed to make divs... hh: %d mm: %d ss: %s", hh, mm, ss);
        console.error(error);
    }
}


/* This section is unique, id of 0 is the string to display, id of 1 is the time we need to count down to.
  The sortValue of id 1 is the current time on the server, which we can diff to stay in sync even if our clocks are bad */
function updateCountdown(id, sortValue, data) {
    if (id === "0") {
        countdownString = data;
    } else if (id === "1") {
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
