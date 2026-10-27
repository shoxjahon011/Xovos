document.addEventListener('DOMContentLoaded', function () {
  var CENTER = [40.20, 68.77];

  function num(v) {
    return parseFloat(String(v).replace(',', '.'));
  }

  function makeMap(beforeRow, hint) {
    var wrap = document.createElement('div');
    wrap.style.cssText = 'margin:10px 0;';
    var note = document.createElement('p');
    note.style.cssText = 'margin:0 0 6px;color:#555;';
    note.textContent = hint;
    var div = document.createElement('div');
    div.style.cssText = 'height:420px;width:100%;max-width:800px;border:1px solid #ccc;';
    wrap.appendChild(note);
    wrap.appendChild(div);
    beforeRow.parentNode.insertBefore(wrap, beforeRow);

    var map = L.map(div).setView(CENTER, 11);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19, attribution: '&copy; OpenStreetMap'
    }).addTo(map);
    return {map: map, wrap: wrap};
  }

  // ---------- JOY va TRANSPORT BEKATI: bitta nuqta ----------
  // Joy sahifasida id_lat/id_lng, Transport sahifasida id_stop_lat/id_stop_lng bor.
  var latEl = document.getElementById('id_lat') || document.getElementById('id_stop_lat');
  var lngEl = document.getElementById('id_lng') || document.getElementById('id_stop_lng');
  if (latEl && lngEl) {
    var row = latEl.closest('.form-row') || latEl.parentNode;
    var m = makeMap(row, "Xaritani bosing: nuqta qo'yiladi va koordinata avtomatik yoziladi. Nuqtani sudrab ham surish mumkin.");
    var marker = null;

    function setMarker(lat, lng, move) {
      if (!marker) {
        marker = L.marker([lat, lng], {draggable: true}).addTo(m.map);
        marker.on('dragend', function () {
          var p = marker.getLatLng();
          fill(p.lat, p.lng);
        });
      } else {
        marker.setLatLng([lat, lng]);
      }
      if (move) m.map.setView([lat, lng], 15);
    }

    function fill(lat, lng) {
      latEl.value = lat.toFixed(6);
      lngEl.value = lng.toFixed(6);
    }

    var lat0 = num(latEl.value), lng0 = num(lngEl.value);
    if (!isNaN(lat0) && !isNaN(lng0)) setMarker(lat0, lng0, true);

    m.map.on('click', function (e) {
      setMarker(e.latlng.lat, e.latlng.lng, false);
      fill(e.latlng.lat, e.latlng.lng);
    });

    function fromInputs() {
      var a = num(latEl.value), b = num(lngEl.value);
      if (!isNaN(a) && !isNaN(b)) setMarker(a, b, true);
    }
    latEl.addEventListener('change', fromInputs);
    lngEl.addEventListener('change', fromInputs);
  }

  // ---------- YO'L: ko'p nuqta ----------
  var coordEl = document.getElementById('id_coordinates');
  if (coordEl) {
    var row2 = coordEl.closest('.form-row') || coordEl.parentNode;
    var colorEl = document.getElementById('id_color');
    var m2 = makeMap(row2, "Yo'lni boshidan oxirigacha xaritani bosib chizing. Har bosish yangi nuqta qo'shadi.");
    var pts = [];
    var line = L.polyline([], {color: colorEl ? colorEl.value : '#c62828', weight: 5}).addTo(m2.map);
    var dots = L.layerGroup().addTo(m2.map);

    function parse() {
      pts = [];
      coordEl.value.split('\n').forEach(function (ln) {
        var p = ln.replace(';', ',').split(',');
        if (p.length >= 2) {
          var a = num(p[0]), b = num(p[1]);
          if (!isNaN(a) && !isNaN(b)) pts.push([a, b]);
        }
      });
    }

    function draw(fit) {
      line.setLatLngs(pts);
      line.setStyle({color: colorEl ? colorEl.value : '#c62828'});
      dots.clearLayers();
      pts.forEach(function (p, i) {
        L.circleMarker(p, {radius: i === 0 || i === pts.length - 1 ? 7 : 4,
          color: '#fff', weight: 2, fillColor: '#222', fillOpacity: 1}).addTo(dots);
      });
      if (fit && pts.length > 1) m2.map.fitBounds(line.getBounds(), {padding: [30, 30]});
    }

    function save() {
      coordEl.value = pts.map(function (p) {
        return p[0].toFixed(6) + ', ' + p[1].toFixed(6);
      }).join('\n');
    }

    var bar = document.createElement('div');
    bar.style.cssText = 'margin-top:6px;';
    function btn(text, fn) {
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = text;
      b.style.cssText = 'margin-right:8px;padding:6px 10px;cursor:pointer;';
      b.onclick = fn;
      bar.appendChild(b);
    }
    btn("↩ Oxirgi nuqtani o'chirish", function () { pts.pop(); save(); draw(false); });
    btn("🗑 Hammasini tozalash", function () {
      if (confirm("Barcha nuqtalar o'chirilsinmi?")) { pts = []; save(); draw(false); }
    });
    m2.wrap.appendChild(bar);

    m2.map.on('click', function (e) {
      pts.push([e.latlng.lat, e.latlng.lng]);
      save();
      draw(false);
    });
    coordEl.addEventListener('change', function () { parse(); draw(true); });
    if (colorEl) colorEl.addEventListener('change', function () { draw(false); });

    parse();
    draw(true);
  }
});