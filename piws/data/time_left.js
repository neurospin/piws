function session_clock(clock_id, cookie_name, expiration_delay, message_format, refresh_rate) {

    // Get the timeout value from the session cookie
    function getCookie(cname) {
        var name = cname + '=';
        var ca = document.cookie.split(';');
        for (var i = 0; i < ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0) == ' ') {
                c = c.substring(1);
            }
            if (c.indexOf(name) == 0) {
                return c.substring(name.length, c.length);
            }
        }
        return '';
    };

    // Deal with optional parameters
    if (typeof message_format === 'undefined') {
        message_format = 'Session will expire in %H:%M:%S';
    }
    if (typeof refresh_rate === 'undefined') {
        refresh_rate = 1000; // in ms
    }

    // Get the expiration value in ms
    var current_value = parseFloat(getCookie(cookie_name)) * 1000;

    // Init the expiration value
    $('#' + clock_id).countdown(current_value + expiration_delay, function(event) {
        $(this).html(event.strftime(message_format));
    });


    // Refresh the expiration value
    setInterval(function() {
        var new_value = parseFloat(getCookie(cookie_name)) * 1000;
        if (new_value != current_value) {
            current_value = new_value;
            $('#' + clock_id).countdown(current_value + expiration_delay);
        }
    }, refresh_rate);
};


/*// Define empty structure
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
    $("#timeh").html(timedisp(timeleft.hours)); }, 1000);*/

