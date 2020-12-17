$( document ).ready(function() {{
	$('.titleColumn0').removeClass("hidden-xs");
	$('.titleColumn0').show();
	$('.rankColumn0').removeClass("hidden-xs");
	$('.rankColumn0').show();
	$('.titleColumn1').removeClass("hidden-xs");
	$('.titleColumn1').show();
	$('.rankColumn1').removeClass("hidden-xs");
	$('.rankColumn1').show();
	$('.titleColumn2').removeClass("hidden-xs");
	$('.titleColumn2').show();
	$('.rankColumn2').removeClass("hidden-xs");
	$('.rankColumn2').show();
	$('.titleColumn3').removeClass("hidden-xs");
	$('.titleColumn3').show();
	$('.rankColumn3').removeClass("hidden-xs");
	$('.rankColumn3').show();
}});

$(function () {
	var i = 1;
	
	$('.rotateButton').click(function () {
		$('.titleColumn').hide();
		$('.rankingColumn').hide();
		$('.titleColumn' + i).addClass("hidden-xs");
		$('.rankColumn' + i).addClass("hidden-xs");
		$('.titleColumn' + (i+1)).addClass("hidden-xs");
		$('.rankColumn' + (i+1)).addClass("hidden-xs");
		$('.titleColumn' + (i+2)).addClass("hidden-xs");
		$('.rankColumn' + (i+2)).addClass("hidden-xs");
		i++;
		var columns = $("#numColumns").val()
		if (i > (columns-3)) {
			i = 1;
		}
		$('.titleColumn' + i).removeClass("hidden-xs");
		$('.titleColumn' + (i+1)).removeClass("hidden-xs");
		$('.titleColumn' + (i+2)).removeClass("hidden-xs");
		$('.rankColumn' + i).removeClass("hidden-xs");
		$('.rankColumn' + (i+1)).removeClass("hidden-xs");
		$('.rankColumn' + (i+2)).removeClass("hidden-xs");
		$('.rankingColumn').show();
		$('.titleColumn' ).show();
	});
});