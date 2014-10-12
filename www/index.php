<html>
<head>
    <title>BISMUTH MINECRAFT</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.7.2/jquery.min.js"></script>
    <style>
    body { width:100%; height: 100%; background-color: #466; font-family: Calibri; padding: 0 20px; margin: 0; overflow: hidden; position: relative; }
    h1 { text-align: center; line-height:25px; margin-bottom: 0px; font-size: 16pt;  }
    table { margin: auto; }
    #header { margin-bottom: 30px; text-align: center; }
    #mapcontainer { position: absolute; margin: auto; text-align: center; left: 261px; top: 0px; }
    #mapcontainer img {
        position: absolute;
        image-rendering:optimizeSpeed;
        image-rendering:-webkit-optimize-contrast;
        image-rendering:-moz-crisp-edges;
        image-rendering:-o-crisp-edges;
        image-rendering:optimize-contrast;
        -ms-interpolation-mode:nearest-neighbor;
    }

    .label {
        position: absolute;
        font-family: Calibri, Verdana, sans-serif;
        font-size: 11px;
        margin-top: -20px;
        background: rgba(255,255,255,0.7);
        padding: 0px 2px;
        border: 1px solid #000;
        white-space: pre;
    }

    .marker {
        position: absolute;
        width: 9px;
        height: 9px;
        margin-top: -4px;
        margin-left: -4px;
    }

    td .marker {
        position: relative;
        margin: auto;
    }

    .marker.x { background-image: url(icon.x.png); }
    .marker.square { background-image: url(icon.square.png); }
    .marker.circle { background-image: url(icon.circle.png); }
    .marker.portal { background-image: url(icon.portal.png); }
    .marker.big_circle { background-image: url(icon.big_circle.png); }
    .marker.mine { background-image: url(icon.mine.png); }
    .marker.farm { background-image: url(icon.farm.png); }
    .marker.keep { background-image: url(icon.keep.png); }
    .marker.tower { background-image: url(icon.tower.png); }
    .marker.ruins { background-image: url(icon.ruins.png); }

    #mapcontrols { border-right: 1px solid #233; background: #fff; position: fixed; top: 0; width: 250px; left: 0px; text-align:left; padding: 0 5px; font-size: 80%; height: 100%; overflow: auto; }
    td { text-align: center; }
    td.sign { background: #b0a080; border: 4px solid #706040; font-size: 11px; line-height: 10px; width: 86px; height: 48px; vertical-align: top; padding: 5px; font-family:monospace; }
    #scale { position: fixed; bottom: 0px; left: 261px; }
    #input-catch { width: 100%; height: 100%; position: fixed; top: 0px; left: 0px; cursor:grab; cursor:-moz-grab; cursor:-webkit-grab; user-select: none; }
    #input-catch.dragging { cursor:grabbing; cursor:-moz-grabbing; cursor:-webkit-grabbing; }
    </style>
</head>
<body>
    <div id="mapcontainer">
        <?php

        $images = array();
        $coords = array();
        $left = 0;
        $top = 0;

        $dir = opendir("./tile");
        $files = array();
        $tiles = array();

        while ($file = readdir($dir)) {
            if (!preg_match("/^tile.*png$/", $file)) continue;
            $files[] = $file;
        }

        function tile_file_cmp($a, $b) {
            $achunks = explode(".", $a);
            $bchunks = explode(".", $b);

            if ( (int)$achunks[1] > (int)$bchunks[1] || ((int)$achunks[1] == (int)$bchunks[1] && (int)$achunks[2] > (int)$bchunks[2]) ) {
                return 1;
            } else {
                return -1;
            }

        }
        usort($files, tile_file_cmp);

        foreach ($files as $file) {
            $chunks = explode(".", $file);

            $tiles[] = array($file, (int)$chunks[1], (int)$chunks[2]);

            if ($chunks[1] < $left) {
                $left = (int)$chunks[1];
            }
            if ($chunks[2] < $top) {
                $top = (int)$chunks[2];
            }
        }

        foreach ($tiles as $tile) {
            $x = ($tile[1] - $left) * 512;
            $y = ($tile[2] - $top) * 512;
            print '<img class="tile" src="tile/'.$tile[0].'" id="tile_'.$tile[1].'_'.$tile[2].'" style="top: '.$y.'px; left: '.$x.'px;">';
            print "\n";
        }

        $markers = json_decode(file_get_contents("./tile/markers.json"));

        foreach ($markers as $k => $region) {
            foreach ($region as $marker) {
                $x = $marker->x - ($left * 512);
                $y = $marker->z - ($top * 512);
                print '<div class="marker '.$marker->type.'" style="top: '.$y.'px; left: '.$x.'px;"></div>';
                if ($marker->label) {
                    $label = str_replace('\\u0027', "'", $marker->label);
                    print '<div class="label" style="top: '.$y.'px; left: '.$x.'px;">'.$label.'</div>';
                }
            }
        }

        ?>

    </div>
    <div id="input-catch">&nbsp;</div>
    <div id="mapcontrols">
        <div id="header">
            <h1>Bismuth Minecraft Server</h1>
            running current vanilla release (1.8.0)
        </div>
        <p>
            <strong>Map Controls</strong><br>
            <input type="checkbox" id="overlay_icons_toggle" checked="checked" onChange="renderLayers();"> Icons<br>
            <input type="checkbox" id="overlay_labels_toggle" checked="checked" onChange="renderLayers();"> Labels<br>
        </p>
        <p>
            <strong>Sign Formats for Markers</strong>
            <table>
                <tr>
                    <td class="sign"><em>&lt;icon text&gt;</em><br>The rest<br>is for<br>the label</td>
                </tr>
            </table>
        </p>
        <p>
            <strong>Available icons</strong>
            <table>
                <tr>
                    <td width="20%">x</td>
                    <td width="10%">&rarr;</td>
                    <td width="20%"><div class="marker x"></div></td>

                    <td width="20%">(*)</td>
                    <td width="10%">&rarr;</td>
                    <td width="20%"><div class="marker circle"></div></td>
                </tr>
                <tr>
                    <td>[*]</td>
                    <td>&rarr;</td>
                    <td><div class="marker square"></div></td>

                    <td>((*))</td>
                    <td>&rarr;</td>
                    <td><div class="marker big_circle"></div></td>
                </tr>
                <tr>
                    <td>(K)</td>
                    <td>&rarr;</td>
                    <td><div class="marker keep"></div></td>

                    <td>(T)</td>
                    <td>&rarr;</td>
                    <td><div class="marker tower"></div></td>
                </tr>
                <tr>
                    <td>(F)</td>
                    <td>&rarr;</td>
                    <td><div class="marker farm"></div></td>

                    <td>(M)</td>
                    <td>&rarr;</td>
                    <td><div class="marker mine"></div></td>
                </tr>
                <tr>
                    <td>^^</td>
                    <td>&rarr;</td>
                    <td><div class="marker portal"></div></td>

                    <td>(R)</td>
                    <td>&rarr;</td>
                    <td><div class="marker ruins"></div></td>
                </tr>
            </table>
        </p>
    </div>
</div>

<script type="text/javascript">
var dragX, dragY, dragMapX, dragMapY;
var topTile = <?php echo $top; ?>;
var leftTile = <?php echo $left; ?>;
var current_zoom = 1;

$body = $('body');

$('#input-catch').mousedown(function(e) {
    dragX = e.clientX;
    dragY = e.clientY;
    dragMapX = document.body.scrollLeft; //parseInt($('#mapcontainer').css('left'), 10);
    dragMapY = document.body.scrollTop; //parseInt($('#mapcontainer').css('top'), 10);
    $('#input-catch').addClass('dragging');
});
$('#input-catch').mouseup(function(e) {
    dragX = dragY = undefined;
    $('#input-catch').removeClass('dragging');
});
$('#input-catch').mouseleave(function(e) {
    dragX = dragY = undefined;
    $('#input-catch').removeClass('dragging');
});
$('#input-catch').mousemove(function(e) {
    if (dragX !== undefined && dragY !== undefined) {
        var $map = $('#mapcontainer');
        var dx = dragX - e.clientX;
        var dy = dragY - e.clientY;

        //$map.css('left', (dragMapX + dx) + 'px');
        //$map.css('top', (dragMapY + dy) + 'px');
        document.body.scrollLeft = dragMapX + dx;
        document.body.scrollTop = dragMapY + dy;
        document.cookie = "" + (document.body.scrollLeft + leftTile * 512) + "," + (document.body.scrollTop + topTile * 512) + "," + current_zoom;
    }
});

var labels = $('.label');
for (i = 0; i < labels.length; i++) {
    rect = labels[i].getBoundingClientRect();
    labels[i].style.marginLeft = -Math.floor(rect.width/2);
}

function renderLayers() {
    var overlays = {
        "icons": {"input":"#overlay_icons_toggle", "selector":".marker"},
        "labels": {"input":"#overlay_labels_toggle", "selector":".label"},
    };

    for ( var k in overlays ) {
        var overlay = overlays[k];
        $(overlay.selector).toggle($(overlay.input)[0].checked);
    }
}

$('body').on('mousewheel', function(event) {
    var delta = event.originalEvent.wheelDeltaY;
    event.preventDefault();
    event.stopPropagation();
    current_zoom = (delta < 0 ? current_zoom * 0.9 : current_zoom / 0.9);
    $('#mapcontainer').css('transform', 'scale(' + current_zoom + ')');
    $('#mapcontainer .label, #mapcontainer .marker').css('transform', 'scale(' + (1 / current_zoom) + ')');
})

$("#input-catch").on("mousewheel", function(event) {
    var delta = event.originalEvent.wheelDeltaY;
    if ( delta > 0 ) {
        zoomBy(2);
    } else {
        zoomBy(.5);
    }
});


if (document.cookie) {
    var coords = document.cookie.split(",");
    document.body.scrollLeft = coords[0] - leftTile * 512;
    document.body.scrollTop = coords[1] - topTile * 512;
    current_zoom = coords[2];
    zoomBy(1);
} else {
    $origin_tile = $('#tile_-1_0');
    origin_left = parseInt($origin_tile.css('left'),10);
    origin_top = parseInt($origin_tile.css('top'),10);
    document.body.scrollLeft = origin_left;
    document.body.scrollTop = origin_top;
}

</script>

</body>
</html>
