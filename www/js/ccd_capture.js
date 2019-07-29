
var lastImageDate = -1;
var continuousMode = 0;

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
	    $("#"+key).html(timeStr + " (" + imageAge + " s old)");
	    // If we have a new image available, display it, otherwise do not
	    // refresh preview image to save bandwidth.
	    if (((val - lastImageDate) > 1) || (lastImageDate==-1)) {
		$("#camera-preview-image").attr("src",imgSrc);
		$("#roi-preview-image").attr("src","/getRoiImage?" + new Date().getTime());
		$("#histogram-image").attr("src","/getFrameHistogram?"+ new Date().getTime());
		$("#x-profile-image").attr("src","/getXProfile?"+ new Date().getTime());
		$("#y-profile-image").attr("src","/getYProfile?"+ new Date().getTime());
		$("#roi-histogram-image").attr("src","/getRoiHistogram?"+ new Date().getTime());
		$("#roi-x-profile-image").attr("src","/getRoiXProfile?"+ new Date().getTime());
		$("#roi-y-profile-image").attr("src","/getRoiYProfile?"+ new Date().getTime());
		lastImageDate = val;
	    }
	    ///////////////////////////////////////////////////
	} else if (key == "statusVal") {
	    var statusStr;
	    switch(val) {
	    case 0:
		statusStr = "No Image";
		break;
	    case 1:
		statusStr = "Ready / Idle";
		break;
	    case 2:
		statusStr = "Exposure in Progress";
		break;
	    case 3:
		statusStr = "Downloading";
		break;
	    default:
		statusStr = "Error - "+val;
	    }
	    $("#status-str").html(statusStr);
	    if ((val==2) || (val==3)) {
		$("#capture-single-image-btn").prop('disabled', true);
	    } else {
		$("#capture-single-image-btn").prop('disabled', false);
	    }
	  
	    /////////////////////////////////////////////////
	} else if (key == "coolerOn") {
	    if (val==true) {
		coolerOn = true
		$("#set-cooler-setpoint-btn").html("Stop Cooler");
	    } else {
		coolerOn = false;
		$("#set-cooler-setpoint-btn").html("Start Cooler");
	    }
	    
	} else {
            $("#"+key).html(val);
        }
    });   
    
};

$(document).ready(function(){
    $("#set-cooler-setpoint-btn").click(function(evt) {
        $('#loading-indicator').show();
        $.post("/setCooler/"+$("#cooler-setpoint").val(),
	       function(data,status) {
		   $('#loading-indicator').hide();
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

    $("#clear-subframe-btn").click(function(evt) {
        $('#loading-indicator').show();
        $.post("/clearSubframe/", function(data,status) {
            $('#loading-indicator').hide();
            //alert("data: "+data);
        });
    });
    

    $("#set-roi-btn").click(function(evt) {
        $('#loading-indicator').show();
	val = $("#roi-origin-x").val() + "," + $("#roi-origin-y").val()
	    + ":" + $("#roi-size-x").val() + "," + $("#roi-size-y").val();
        $.post("/setRoi/"+val, function(data,status) {
            $('#loading-indicator').hide();
            //alert("data: "+data);
        });
    });
    
    $("#clear-roi-btn").click(function(evt) {
        $('#loading-indicator').show();
        $.post("/clearRoi/", function(data,status) {
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

    $("#capture-continuous-btn").click(function(evt) {
        $('#loading-indicator').show();
	if (continuousMode == 0){
	    $("#capture-continuous-btn").html("Stop");
	    continuousMode = 1;
            $.post("/startContinuousExposures/", function(data,status) {
                $('#loading-indicator').hide();
            //alert("data: "+data);
            });
	} else {
	    $("#capture-continuous-btn").html("Start");
	    continuousMode = 0;
            $.post("/stopContinuousExposures/", function(data,status) {
                $('#loading-indicator').hide();
	    });
	}
    });
    
    $("#save-image-btn").click(function(evt) {
        $('#loading-indicator').show();
	val = $("#fname-input").val()
        $.post("/saveImage/"+val, function(data,status) {
            $('#loading-indicator').hide();
            //alert("data: "+data);
        });
    });

    $("#autosave-chk").click(function(evt) {
        $('#loading-indicator').show();
	val = $("#fname-input").val()
	if($("#autosave-chk").is(':checked')) {
            $.post("/startAutoSave/"+val, function(data,status) {
		$('#loading-indicator').hide();
		//alert("data: "+data);
            });
	} else {
            $.post("/stopAutoSave/", function(data,status) {
		$('#loading-indicator').hide();
		//alert("data: "+data);
            });
	}
    });

    
    setInterval("getData();",1000);
    getData();
});        
