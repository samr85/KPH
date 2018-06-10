'use strict';

function alertHandler(message) {
	console.log("Alert: " + message)
}

function logError(message)
{
    message = "Error: " + message;
    addLogMessage(message);
}

function addLogMessage(message)
{
    console.log(message);
}