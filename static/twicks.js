var qcounts = {};
var reconnect = true;

$(document).ready(function () {
    var host = window.location.host;
    host = host.replace(/\:.*/,'');
    var s = new WebSocket('ws://localhost:8888/ws');
    // new io.Socket(host, {port: 8888, rememberTransport: false, connectTimeout: 10000, transports: ['websocket']});
    var paused = false;

    s.onopen = function (transport) {
        console.log(transport);
        $('#status').html("Connecting via " + transport + "...");
    };
    
    s.onmessage = function (evt) {
        var data = evt.data;
        var d = $.parseJSON(data);
        console.log(evt.data);
        console.log(d);

        if (d.type == 'error') {
            reconnect = false;
            s.disconnect();
            alert(d.message);
            return;
        }

        if (d.type == 'welcome') {
            $('#status').html(d.message);
            return;
        }

        if (paused) {
            return;
        }

        var m = d['m'];
        var queue = m.tag;

        $('#count').html(''+m.user_count);

        if (!queue) {
            queue='raw';
        }

        var target = $("#queue_"+queue);
        if (target) {

        var processed_text = m.message;
        processed_text = processed_text.replace(/(http:\/\/[^ ]+)/g, '<a href="$1" target="_blank">$1</a>');
        processed_text = processed_text.replace(/#([^ ]+)/g, '<a href="http://search.twitter.com/search?q=%23$1" target="_blank">#$1</a>');
            var dom = '<div class="message" id="m_'+m.id+'_'+queue+'"><div class="from_user"><a href="http://twitter.com/'+m.from+'" target="_blank"><img class="profile_image" src="'+m.profile_image+'" /></a></div><div>'+processed_text+'</div>';
            if (queue == 'raw') {
                dom += '<div class="buttons">';
                dom += '<button class="tag_button" onclick="tag(\''+m.id+'\',\'damage\')">damage</button>';
                dom += '<button class="tag_button" onclick="tag(\''+m.id+'\',\'advice\')">advice</button>';
                dom += '<button class="tag_button" onclick="tag(\''+m.id+'\',\'requests\')">requests</button>';
                dom += '</div>';
            }
            var e = $(dom);

            if (qcounts[queue]) {
                qcounts[queue]+=1;
            } else {
                qcounts[queue] = 1;
            }

            if (qcounts[queue] >= 30) {
                e.hide();
            }
            target.prepend(e);
            if (qcounts[queue] >= 30) {
                e.fadeIn();
            }


            if (qcounts[queue] > 30) {
                //console.log("Queue " + queue + " too long (" + qcounts[queue] + ")");
                target.children().last().remove();
                qcounts[queue] -= 1;
            }
        }
    };
    s.onclose = function (e) {
        $('#status').html("Disconnected");
        if (reconnect) {
            alert("The connection to the server has been lost. Will try to reconnect");
            window.location.reload();
        }
    };

    $('#status').html("Connecting...")

    $('#rate_select').change(function (e) {
        console.log("Change of rate detected");
        s.send(JSON.stringify({'type': 'options', 'rate': $('#rate_select').val()}));
        console.log("Change of rate sent");
    });

    $('#pause_button').click(function (e) {
        if (paused) {
            paused = false;
            $('#pause_button').html('Pause');
        } else {
            paused = true;
            $('#pause_button').html('Unpause');
        }
    });
    // Ping every 10 seconds just to let them know we're here
    setInterval(function () { console.log("Ping"); s.send(JSON.stringify({'type': 'ping'})); },10000);


});

function tag(id, tag) {
    $('#m_'+id+'_raw').addClass("tagged");
    $.post('/update',{'id':id, 'tag':tag});
    return false;
}
