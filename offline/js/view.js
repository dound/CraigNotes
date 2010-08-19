YUI().use('event-base', 'event-key', 'io-base', 'node-base', 'node-style', function(Y) {
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
        // no-op
    }
    Y.on('io:complete', complete, Y);

    var COMMENT_STATES = {}; // maps cid -> (btn, editing)
    var RATINGS = {};        // maps cid -> (rating, star nodes)

    /** show the editing pane if it is hidden, otherwise update the cmt with the edit pane text */
    function edit_ad_cmt(cid, btn) {
        var state = COMMENT_STATES[cid];
        var txt = Y.one('#cmttxt'+cid);
        if(state.editing) {
            // save the new comment (if it changed)
            btn.set('innerHTML', 'Edit Notes');
            state.editing = false;
            var new_text = Y.one('#cmtedit' + cid).get('value');
            if(new_text !== state.old_text) {
                do_ajax('POST', 'note='+encodeURIComponent(new_text), '/ajax/comment/' + cid);
                if(new_text === '') {
                    txt.set('innerHTML', 'no notes yet');
                }
                else {
                    txt.set('innerHTML', new_text);
                }
            }
            state.old_text = null;

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

            // monitor the text area to make sure it does not get too long
            (function (btn, cid) {
                var cmtedit = Y.one('#cmtedit'+cid);
                var div_charsleft = Y.one('#charsleft'+cid);
                div_charsleft.setStyle('display', '');
                cmtedit.on('key', function(e) {
                    var n = cmtedit.get('value').length;
                    var left = 10000 - n;
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
        COMMENT_STATES[cid] = {'btn':btn, 'editing':false};
    })();}
});
