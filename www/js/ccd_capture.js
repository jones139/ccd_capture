
var lastImageDate = new Date().getTime()/1000;

function getData() {
    $.ajax({url:"/getData",success:updateDashboard});
};

function updateDashboard(dataStr) {
    //alert (dataStr);
    obj = JSON.parse(dataStr)
    $("#cooler-on-checkbox").prop('checked', obj['coolerOn']);
    
    // This populates the <span> elements that have the same id
    // as the object keys.
    $.each(obj, function(key, val) {
        // alert(key + " : " +val);
	if(key == "curImageTime") {
	    var date = new Date(val*1000);
	    var hours = "0" +date.getHours();
	    var minutes = "0" + date.getMinutes();
	    var seconds = "0" + date.getSeconds();
	    var timeStr = hours.substr(-2) + ':' + minutes.substr(-2) + ':' + seconds.substr(-2);
	    var imageAge = Math.floor(new Date().getTime()/1000 - val)
	    var imgSrc = "/getImage?"+ new Date().getTime();
	    $("#"+key).html(timeStr + " (" + imageAge + " s old) - imgSrc="+ imgSrc);
	    // If we have a new image available, display it, otherwise do not
	    // refresh preview image to save bandwidth.
	    if ((val - lastImageDate) > 1) {
		$("#camera-preview-image").attr("src",imgSrc);
		$("#histogram-image").attr("src","/getFrameHistogram?"+ new Date().getTime());
		lastImageDate = val;
	    }
	} else {
            $("#"+key).html(val);
        }
    });   
    
};

$(document).ready(function(){
    $("#set-cooler-setpoint-btn").click(function(evt) {
        $('#loading-indicator').show();
        $.post("/setCooler/"+$("#cooler-setpoint").val(), function(data,status) {
            $('#loading-indicator').hide();
            //alert("data: "+data);
        });
    });
    
    $("#set-exposure-btn").click(function(evt) {
        $('#loading-indicator').show();
        $.post("/setExposureTime/"+$("#exposure-input").val(), function(data,status) {
            $('#loading-indicator').hide();
            //alert("data: "+data);
        });
    });
    
    $("#set-subframe-btn").click(function(evt) {
        $('#loading-indicator').show();
	val = $("#subframe-origin-x").val() + "," + $("#subframe-origin-y").val()
	    + ":" + $("#subframe-size-x").val() + "," + $("#subframe-size-y").val();
        $.post("/setSubframe/"+val, function(data,status) {
            $('#loading-indicator').hide();
            //alert("data: "+data);
        });
    });
    
    $("#capture-single-image-btn").click(function(evt) {
        $('#loading-indicator').show();
        $.post("/startExposure/", function(data,status) {
            $('#loading-indicator').hide();
            //alert("data: "+data);
        });
    });
    
    
    setInterval("getData();",1000);
    getData();
});        
