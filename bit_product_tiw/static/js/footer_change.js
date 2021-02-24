function footer() {
    var x = document.getElementsByClassName("footer");
    var arr = Array.prototype.slice.call(x);
    arr.pop();
    if (arr.length > 2) {
        for (var i = 0; i < arr.length; i++) {
            x[i].style.visibility = "hidden";
        }

    }
}


