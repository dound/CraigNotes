YUI().use('event-base', 'event-key', 'io-base', 'node-base', 'node-style', 'yui2-editor', function(Y) {
    // AJAX request constants
    var REQUEST_HEADERS = {"Pragma":"no-cache",
                           "Cache-Control":"no-store, no-cache, must-revalidate, post-check=0, pre-check=0",
                           "Expires":0,
                           "Last-Modified":new Date(0),
                           "If-Modified-Since":new Date(0)};
    var REQUEST_CFG = {headers:REQUEST_HEADERS};
    function do_ajax(method, data, uri) {
        REQUEST_CFG.method = method;
        REQUEST_CFG.data = data;
        Y.io(uri, REQUEST_CFG);
    }

	/** callback issued when an AJAX call completes */
	function complete(id, o) {
		var ret = o.responseText;
		if(ret === 'not-ready') {
			// check for new ads again (in a little bit)
			setTimeout(function () { check_for_ads(); }, 10000);
		}
		else if(ret === 'ready0') {
			if(REFRESH_WHEN_RESULTS_AVAIL) {
				Y.one('#soon').innerHTML = "No ads meet this criteria.";
			}
			Y.one('#age').innerHTML = 'less than 1 minute ago (no new ads)';
		}
		else if(ret.substring(0,5) === 'ready') {
			if(REFRESH_WHEN_RESULTS_AVAIL) {
				window.location.reload();
			}
			Y.one('#age').innerHTML = '<span id="newresults">there are ' + ret.substring(5) + ' new/updated ads - refresh to see them</span>';
		}
	}
	Y.on('io:complete', complete, Y);

	// check for ads asynchronously if we know the feed is being updated and we don't have any ads yet
	var check_count = 0;
	function check_for_ads() {
		// only do 3 checks if we have no results, or 1 check if we have some results
		if((REFRESH_WHEN_RESULTS_AVAIL && check_count < 3) || check_count==0) {
			do_ajax('POST', 'feed='+encodeURIComponent(FEED), '/ajax/is_feed_ready');
			check_count += 1;
		}
		else if(REFRESH_WHEN_RESULTS_AVAIL) {
			Y.one('#soon').innerHTML = "No ads meet this criteria.";
		}
	}
	if(REFRESH_WHEN_RESULTS_AVAIL) {
		setTimeout(function () { check_for_ads(); }, 5000);
	}
	else if(UPDATING_SHORTLY) {
		// check in 2 minutes to see if the update resulted in any new results
		setTimeout(function () { check_for_ads(); }, 120000);
	}

    var COMMENT_STATES = {}; // maps cid -> (btn, editor)
    var RATINGS = {};        // maps cid -> (rating, star nodes)

	var EDITOR_CFG = {
		height: '100px',
		width: '100%',
		animate: false,
		dompath: false,
		focusAtStart: true,
		autoHeight: true,
		toolbar: {
			collapse: false,
			titlebar: '',
			draggable: false,
			buttonType: 'advanced',
			buttons: [
				{ group: 'fontstyle', label: 'Font Name and Size',
					buttons: [
						{ type: 'select', label: 'Arial', value: 'fontname', disabled: true,
							menu: [
								{ text: 'Arial', checked: true },
								{ text: 'Arial Black' },
								{ text: 'Comic Sans MS' },
								{ text: 'Courier New' },
								{ text: 'Lucida Console' },
								{ text: 'Tahoma' },
								{ text: 'Times New Roman' },
								{ text: 'Trebuchet MS' },
								{ text: 'Verdana' }
							]
						},
						{ type: 'spin', label: '13', value: 'fontsize', range: [ 9, 75 ], disabled: true }
					]
				},
				{ type: 'separator' },
				{ group: 'textstyle', label: 'Font Style',
					buttons: [
						{ type: 'push', label: 'Bold CTRL + SHIFT + B', value: 'bold' },
						{ type: 'push', label: 'Italic CTRL + SHIFT + I', value: 'italic' },
						{ type: 'push', label: 'Underline CTRL + SHIFT + U', value: 'underline' },
						{ type: 'separator' },
						{ type: 'color', label: 'Font Color', value: 'forecolor', disabled: true },
						{ type: 'color', label: 'Background Color', value: 'backcolor', disabled: true },
						{ type: 'separator' },
						{ type: 'push', label: 'Remove Formatting', value: 'removeformat', disabled: true },
						{ type: 'push', label: 'Show/Hide Hidden Elements', value: 'hiddenelements' },
						{ type: 'separator' },
						{ type: 'push', label: 'Undo', value: 'undo', disabled: true },
						{ type: 'push', label: 'Redo', value: 'redo', disabled: true }
					]
				},
				{ type: 'separator' },
				{ group: 'alignment', label: 'Alignment',
					buttons: [
						{ type: 'push', label: 'Align Left CTRL + SHIFT + [', value: 'justifyleft' },
						{ type: 'push', label: 'Align Center CTRL + SHIFT + |', value: 'justifycenter' },
						{ type: 'push', label: 'Align Right CTRL + SHIFT + ]', value: 'justifyright' },
						{ type: 'push', label: 'Justify', value: 'justifyfull' }
					]
				},
				{ type: 'separator' },
				{ group: 'indentlist', label: 'Indenting/Lists',
					buttons: [
						{ type: 'push', label: 'Indent', value: 'indent', disabled: true },
						{ type: 'push', label: 'Outdent', value: 'outdent', disabled: true },
						{ type: 'push', label: 'Create an Unordered List', value: 'insertunorderedlist' },
						{ type: 'push', label: 'Create an Ordered List', value: 'insertorderedlist' }
					]
				},
				{ type: 'separator' },
				{ group: 'insertitem', label: 'Insert Item',
					buttons: [
						{ type: 'push', label: 'HTML Link CTRL + SHIFT + L', value: 'createlink', disabled: true },
						{ type: 'push', label: 'Insert Image', value: 'insertimage' }
					]
				}
			]
		}
	};

    /** show the editing pane if it is hidden, otherwise update the cmt with the edit pane text */
    function edit_ad_cmt(cid, btn) {
        var state = COMMENT_STATES[cid];
        var txt = Y.one('#cmttxt'+cid);
        if(state.editor) {
            // save the new comment (if it changed)
            btn.set('innerHTML', 'Edit Notes');
			state.editor.saveHTML();
			var new_text = state.editor.get('element').value;
            state.editor = null;
            if(new_text !== state.old_text) {
                do_ajax('POST', 'note='+encodeURIComponent(new_text), '/ajax/comment/' + cid);
	            state.old_text = null;
			}

			if(new_text === '') {
				txt.set('innerHTML', 'no notes yet');
			}
			else {
				txt.set('innerHTML', new_text);
			}

            var div_charsleft = Y.one('#charsleft'+cid);
            div_charsleft.setStyle('display', 'none');
        }
        else {
            // start editing the comment
            btn.set('innerHTML', 'Save Notes');
            state.editing = true;
            state.old_text = txt.get('innerHTML');
            if(state.old_text === 'no notes yet') {
                state.old_text = '';
            }
            txt.set('innerHTML', '<textarea id="cmtedit' + cid + '" rows="5" style="width:100%">' + state.old_text + '</textarea>');

            (function (btn, cid) {
				var editor = new Y.YUI2.widget.Editor('cmtedit' + cid, EDITOR_CFG);
				state.editor = editor;
				editor.render();

		        // monitor the text area to make sure it does not get too long
	            var cmtedit = Y.one('#cmtedit'+cid);
                var div_charsleft = Y.one('#charsleft'+cid);
                div_charsleft.setStyle('display', '');
				editor.on('editorKeyUp', function(e) {
					editor.saveHTML();
                    var n = editor.get('element').value.length;
                    var left = 32000 - n;
                    if(left < 1000) {
                        if(left < 0) {
                            div_charsleft.setStyle('color', 'red');
                            btn.setStyle('display', 'none');
							var extra = -left;
							div_charsleft.set('innerHTML', extra + ' characters too long.');
                        }
                        else {
                            div_charsleft.setStyle('color', '');
                            btn.setStyle('display', '');
                          	div_charsleft.set('innerHTML', left + ' characters left');
                        }
                    }
                    else {
                        div_charsleft.set('innerHTML', '');
                        btn.setStyle('display', '');
                    }
                }, 'up:');
            })(btn, cid);
        }
    }

    /** update the rating for the specified ad */
    function rate(cid, rating) {
        var rating_info = RATINGS[cid];
        var new_rating = rating;
        if(rating_info.stars[rating].hasClass('starsel')) {
            if(rating_info.rating === rating) {
                // clicking star when it is the highest one selected => deselect all stars
                new_rating = 0;
            }
        }
        rating_info.rating = new_rating;
        for(var i=1; i<=5; i++) {
            if(i <= new_rating) {
                rating_info.stars[i].replaceClass('star', 'starsel');
            }
            else {
                rating_info.stars[i].replaceClass('starsel', 'star');
            }
        }
        do_ajax('POST', '', '/ajax/rate/' + cid + '/' + new_rating);
    }

    /** hide or unhide an ad */
    function toggle_hide_ad(cid) {
        var div_header = Y.one('#header'+cid);
        var row_desc = Y.one('#desc'+cid);
        var row_cmt = Y.one('#cmtrow'+cid);
        var hide_btn = Y.one('#hide'+cid);

        var less_prom = div_header.hasClass('lessprom');
        var hidden = (SHOW_HIDDEN_ADS ? !less_prom : less_prom);
        if(hidden) {
            do_ajax('POST', '', '/ajax/unhide/' + cid);
            hide_btn.set('innerHTML', "Hide This Ad");
        } else {
            do_ajax('POST', '', '/ajax/hide/' + cid);
            hide_btn.set('innerHTML', "Don't Hide This Ad");
        }

        if(less_prom) {
            div_header.removeClass('lessprom');
            row_desc.setStyle('display', '');
            row_cmt.setStyle('display', '');

        }
        else {
            div_header.addClass('lessprom');
            row_desc.setStyle('display', 'none');
            row_cmt.setStyle('display', 'none');
        }
    }

    // hookup each ad's widgets
    for(var i=0; i<CIDS.length; i++) { (function () {
        var cid = CIDS[i];

        // initalize the stars
        var stars = [];
        var rating_info = {'rating':0, 'stars':stars};
        for(var j=1; j<=5; j++) { (function () {
            var rating = j;
            var star = Y.one('#star' + j + '_' + cid);
            star.on('click', function(e) { rate(cid, rating); } );
            stars[j] = star;
            if(star.hasClass('starsel')) {
                rating_info.rating = j;
            }
        })();}
        RATINGS[cid] = rating_info;

        // initalize the hide/unhide button
        var btn = Y.one('#hide' + cid);
        btn.on('click', function(e) { toggle_hide_ad(cid); } );

        // initalize the edit comments button
        var btn = Y.one('#edit' + cid);
        btn.on('click', function(e) { edit_ad_cmt(cid, btn); } );
        COMMENT_STATES[cid] = {'btn':btn, 'editor':null};
    })();}
});
