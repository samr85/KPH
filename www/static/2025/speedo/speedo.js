/* id will be "extraData" sortValue and data are the 2nd and 3rd parameters returned by requestSection in extraDiv.py */
function updateExtraDiv(id, sortValue, data) {
    active = data.split(",")
    if (active.indexOf("base") == -1) {
        $("#speedo_main").css("display", "none")
    } else {
        $("#speedo_main").css("display", "block")
    }

    for (let i = 1; i < 3; i++) {
        for (let j = 1; j < 8; j++) {
            index = `${i}${j}`
            if (active.indexOf(index) == -1) {
                $(`#speedo_${index}`).css("display", "none")
            } else {
                $(`#speedo_${index}`).css("display", "block")
            }
        }
    }
}

initialiseSection("speedo", updateExtraDiv, [])