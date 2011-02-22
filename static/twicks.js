var qcounts = {};
var reconnect = true;

$(document).ready(function () {
    var host = window.location.host;
    host = host.replace(/\:.*/,'');
    var s = new io.Socket(host, {port: 8888});


    s.connect();
    s.addEvent('message', function (data) {


        var d = $.parseJSON(data);

        if (d.type == 'error') {
            reconnect = false;
            s.disconnect();
            alert(d.message);
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
            e.hide();
            target.prepend(e);
            e.fadeIn();

            if (qcounts[queue]) {
                qcounts[queue]+=1;
            } else {
                qcounts[queue] = 1;
            }

            if (qcounts[queue] > 30) {
                console.log("Queue " + queue + " too long (" + qcounts[queue] + ")");
                target.children().last().remove();
                qcounts[queue] -= 1;
            }
        }
    });
    s.addEvent('disconnect', function (e) {
        if (reconnect) {
            alert("The connection to the server has been lost. Will try to reconnect");
            window.location.reload();
        }
    });

    $('#rate_select').change(function (e) {
        console.log("Change of rate detected");
        s.send({'type': 'options', 'rate': $('#rate_select').val()});
        console.log("Change of rate sent");
    });

});

function tag(id, tag) {
    $('#m_'+id+'_raw').addClass("tagged");
    $.post('/update',{'id':id, 'tag':tag});
    return false;
}
