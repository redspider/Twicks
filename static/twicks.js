var qcounts = {};

$(document).ready(function () {
    var s = new io.Socket("localhost", {port: 8888});
    s.connect();
    s.addEvent('message', function (data) {
        var d = $.parseJSON(data);
        var m = d['m'];
        var queue = m.tag;
        if (!queue) {
            queue='raw';
        }
        console.log("Message received",m,queue);

        var target = $("#queue_"+queue);
        console.log("#queue_"+queue, target);
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
});

function tag(id, tag) {
    $('#m_'+id+'_raw').addClass("tagged");
    $.post('/update',{'id':id, 'tag':tag});
    return false;
}
