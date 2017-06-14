

jQuery(document).ready(function($){

	$(window).on( 'load resize', function() {

		// Explore dotted lines
		if ($('#home-explore-path').length > 0) {

			var trail = $('#home-explore-path');
			var trail2 = $('#explored-path');
            var distance_from_bottom = -(
                mezr.height(document, 'content') + mezr.place($(".more")[0]).top);

		}

		// draw trail 2 as you scroll
		if ($('#explored-path').length > 0) {

			var path = document.querySelector('#explored-path');
			var pathLength = path.getTotalLength();
			path.style.strokeDasharray = pathLength + ' ' + pathLength;
			path.style.strokeDashoffset = pathLength;
			path.getBoundingClientRect();

			if( pathLength > 1500 ) {

				window.addEventListener("scroll", function (e) {

					var scrollPercentage = (document.documentElement.scrollTop + document.body.scrollTop) / ((document.documentElement.scrollHeight - ( distance_from_bottom ) ) - document.documentElement.clientHeight);

					var drawLength = pathLength * scrollPercentage;
					path.style.strokeDashoffset = pathLength - drawLength;

					if (scrollPercentage > 0.99) {
						path.style.strokeDasharray = "none";
					} else {
						path.style.strokeDasharray = pathLength + ' ' + pathLength;
					}

				});
			} else {
				window.addEventListener("scroll", function (e) {

					var scrollPercentage = (document.documentElement.scrollTop + document.body.scrollTop) / ((document.documentElement.scrollHeight ) - document.documentElement.clientHeight);

					var drawLength = pathLength * scrollPercentage;
					path.style.strokeDashoffset = pathLength - drawLength;

					if (scrollPercentage > 40) {
						path.style.strokeDasharray = "none";
					} else {
						path.style.strokeDasharray = pathLength + ' ' + pathLength;
					}

				});
			}
		}


	});

});





