
function submitAnswer(question)
{
    if ($("#" + question + "Answer")[0].value)
    {
        sendMessage("subAnswer " + question + " " + window.btoa($("#" + question + "Answer")[0].value));
    }
    else
    {
        logError("Please enter an answer to submit");
    }
}

function requestHint(question)
{
    sendMessage("reqHint " + question);
}

initialiseSection("question", standardSection("questionList"), []);