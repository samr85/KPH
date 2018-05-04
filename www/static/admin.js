
function mark(id, mark) {
    teamName = $("#teamName" + id)[0]
    questionName = $("#questionName" + id)[0] 
    correct = $("#correct" + id)[0]
    override = $("#override" + id)[0]
    score = $("#score" + id)[0]
    if (!(teamName && questionName && correct && override)) {
        errorHandler("an element doesn't exist for marking id:" + id)
        return
    }

    if (mark != correct.value && !override.checked) {
        errorHandler("Attempting to mark question unexpectedly without ticking to override")
        return
    }

    if (score !== undefined){
        if (!score.value) {
            errorHandler("question has custom scoring, but no score specified")
            return
        }
        sendMessage("markAnswer " + teamName.value + " " + questionName.value + " " + mark + " " + score.value)
    }
    else {
        sendMessage("markAnswer " + teamName.value + " " + questionName.value + " " + mark)
    }
}

initialiseSection("answerQueue", standardSection("answerQueue"), [])
