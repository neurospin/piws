
// Define empty structure
var timeleft = {}

// Two digits display
function timedisp(value) {
    if (value < 10) {
        value = "0" + value;
    }
    return value;
}

// Update time left display every second
time = setInterval( function() {
    timeleft.seconds--;
    if (timeleft.seconds == 0 && timeleft.minutes == 0 && timeleft.hours == 0) {
        window.location.href = timeleft.redirecturl;
        clearInterval(time);
        return
    }
    if(timeleft.seconds < 0) {
        timeleft.minutes--;
        timeleft.seconds = 59;
    }
    if(timeleft.minutes < 0) {
        timeleft.hours--;
        timeleft.minutes = 59;
    }
    $("#times").html(timedisp(timeleft.seconds)); 
    $("#timem").html(timedisp(timeleft.minutes)); 
    $("#timeh").html(timedisp(timeleft.hours)); }, 1000);

