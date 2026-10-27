(function () {
  function clientId() {
    var id = null;
    try { id = localStorage.getItem('xovos_client'); } catch (e) {}
    if (!id) {
      id = (window.crypto && crypto.randomUUID)
        ? crypto.randomUUID()
        : String(Date.now()) + Math.random().toString(16).slice(2);
      try { localStorage.setItem('xovos_client', id); } catch (e) {}
    }
    return id;
  }

  function csrf() {
    var m = document.querySelector('meta[name="csrf"]');
    return m ? m.content : '';
  }

  function mine(id) {
    try { return parseInt(localStorage.getItem('xovos_rate_' + id), 10) || 0; }
    catch (e) { return 0; }
  }

  window.starsText = function (avg) {
    var n = Math.max(0, Math.min(5, Math.round(Number(avg) || 0)));
    return '★'.repeat(n) + '☆'.repeat(5 - n);
  };

  window.initRating = function (box, placeId, avg, cnt) {
    if (!box) return;
    avg = Number(avg) || 0;
    cnt = Number(cnt) || 0;
    var my = mine(placeId);
    var note = '';

    function draw() {
      var sum = cnt
        ? '<span class="sum">' + window.starsText(avg) + ' ' + avg.toFixed(1) +
          '</span> <small>(' + cnt + ' ta baho)</small>'
        : '<span class="sum">Hali baholanmagan</span>';
      box.innerHTML = '<div>' + sum + '</div>' +
        '<div class="ask">' + (my ? 'Sizning bahoingiz:' : 'Baholang:') + '</div>' +
        '<div class="pick"></div><div class="msg"></div>';
      var pick = box.querySelector('.pick');
      for (var i = 1; i <= 5; i++) {
        (function (n) {
          var b = document.createElement('button');
          b.type = 'button';
          b.textContent = '★';
          b.setAttribute('aria-label', n + ' yulduz');
          if (n <= my) b.className = 'on';
          b.onclick = function () { send(n); };
          pick.appendChild(b);
        })(i);
      }
      box.querySelector('.msg').textContent = note;
    }

    function send(n) {
      fetch('/api/joy/' + placeId + '/baho/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf()},
        body: JSON.stringify({stars: n, client_id: clientId()})
      })
        .then(function (r) {
          return r.json().then(function (d) { return {ok: r.ok, d: d}; });
        })
        .then(function (res) {
          if (!res.ok) throw new Error('bad');
          avg = res.d.avg;
          cnt = res.d.count;
          my = n;
          try { localStorage.setItem('xovos_rate_' + placeId, String(n)); } catch (e) {}
          note = 'Rahmat! Bahoyingiz saqlandi.';
          draw();
        })
        .catch(function () {
          note = "Saqlab bo'lmadi. Internetni tekshiring.";
          draw();
        });
    }

    draw();
  };
})();