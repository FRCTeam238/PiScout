$(document).ready(function () {{
	$("#teamNumberFilter").keyup(function () {{
	  processFilter();
	  return false;
	}});
	$("#teamFilter").submit(function () {{
	  processFilter();
	  return false;
	}});
	$('#teamFilter').on('reset', function (e) {{
	  resetFilter();
	}});
	$('#noTeamsInFilter').attr("style", "display: none !important");//hide on load
	var urlTeamFilter = getUrlParameter('n');
	if (urlTeamFilter != null && urlTeamFilter.length > 0) {{
	  $('#teamNumberFilter').val(urlTeamFilter);
	  processFilter();
	}}
	}});

	function processFilter() {{
	var ttf = $('#teamNumberFilter').val();
	if (ttf == "") {{
	resetFilter();
	return false;
	}}
	$('#matches > tbody  > tr').each(function () {{
	var showRow = false;
	var targetID = $(this).attr('id');
	$("td[id^=team]", this).each(function () {{
		var m = $(this).text().trim();
		if (m == ttf) {{
			showRow = true;
		}}
	}});
	if (!showRow) {{//end of row
		$('#' + targetID).attr("style", "display: none !important");
	}}
	else {{
		$('#' + targetID).attr("style", "display: inline-list-item !important");
	}}
	showRow = false;//reset
	}});
	var totalRow = $('#matches tr:visible').length;
	if (totalRow <= 1) {{//1=header
	$('#noTeamsInFilterNumber').html(ttf);
	$('#noTeamsInFilter').attr("style", "display: inline-list-item !important");
	}}
	else {{
	$('#noTeamsInFilter').attr("style", "display: none !important");
	}}
	}}
	function resetFilter() {{
	$('#matches > tbody  > tr').each(function () {{
	var targetID = $(this).attr('id');
	$('#' + targetID).attr("style", "display: inline-list-item !important");
	$('#noTeamsInFilter').attr("style", "display: none !important");
	}});
	}}
	function getUrlParameter(sParam) {{
	var sPageURL = decodeURIComponent(window.location.search.substring(1)),
	sURLVariables = sPageURL.split('&'),
	sParameterName,
	i;
	for (i = 0; i < sURLVariables.length; i++) {{
	sParameterName = sURLVariables[i].split('=');

	if (sParameterName[0] === sParam) {{
		return sParameterName[1] === undefined ? true : sParameterName[1];
	}}
	}}
	}};