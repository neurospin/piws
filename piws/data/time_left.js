// Get the timeout value from the session cookie
function getCookie(cookie_name) {
    var name = cookie_name + '=';
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


// Two digits display
function timedisp(value) {
    if (value < 10) {
        value = "0" + value;
    }
    return value;
}


// Define empty structure
var cookie_name = "";
var last_cookie_time = -1;
var current_time = -1;
var expiration_time = -1;

// Update time left display every second
time = setInterval( function() {

    var cookie_time = parseFloat(getCookie(cookie_name)) * 1000;
    if (!isNaN(cookie_time) && expiration_time != -1) {
        if (last_cookie_time != cookie_time) {
            // in ms
            current_time = expiration_time - (new Date().getTime() - cookie_time);
            last_cookie_time = cookie_time;
        } else {
            current_time -= 1000;
        }
        if (current_time < 0) {
            current_time = 0;
            var hh = 0;
            var mm = 0;
            var ss = 0;
        } else {
            var date = new Date(current_time);
            var hh = date.getUTCHours();
            var mm = date.getUTCMinutes();
            var ss = date.getSeconds();
        }    
        $("#times").html(timedisp(ss)); 
        $("#timem").html(timedisp(mm)); 
        $("#timeh").html(timedisp(hh)); }
    }, 1000);

