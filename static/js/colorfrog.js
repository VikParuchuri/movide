/*
* Initialise the Google Map in the footer
*/
function initialize() {
	var mapOptions = {
		center: new google.maps.LatLng(60.170421,24.938149), 
		zoom: 15,
		panControl: false,
		zoomControl: false,
		mapTypeControl: false,
		scaleControl: false,
		scrollwheel: false,
		streetViewControl: false,
		overviewMapControl: false,
		mapTypeId: google.maps.MapTypeId.ROADMAP
	};
	
	//styling the map
	var styleOptions = {
		name: "Dummy Style"
	};

	var MAP_STYLE = [
		{
			"stylers": [
				{ "saturation": -100 },
				{ "visibility": "on" },
				{ "lightness": 40 }
			]
		}
	]
	
	var map = new google.maps.Map(document.getElementById("footer-map"), mapOptions);
	var mapType = new google.maps.StyledMapType(MAP_STYLE, styleOptions);
	map.mapTypes.set("Dummy Style", mapType);
	map.setMapTypeId("Dummy Style");
	
	var center;
	function calculateCenter() {
		center = map.getCenter();
	}
	google.maps.event.addDomListener(map, 'idle', function() {
		calculateCenter();
	});
	google.maps.event.addDomListener(window, 'resize', function() {
		map.setCenter(center);
	});
	
	var image = '../img/icon-map-marker.png';
  	var myLatLng = new google.maps.LatLng(60.16992,24.938707);
	var customMarker = new google.maps.Marker({
	  position: myLatLng,
	  map: map,
	  icon: image
	});
}

var style = 'blue';

//FitVids
$(function($){ $('.mediaVideo').fitVids(); });