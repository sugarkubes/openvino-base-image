const postData = (url = ``, data = {}) => {
  // Default options are marked with *
    return fetch(url, {
        method: "POST", // *GET, POST, PUT, DELETE, etc.
        // mode: "cors", // no-cors, cors, *same-origin
        // cache: "no-cache", // *default, no-cache, reload, force-cache, only-if-cached
        // credentials: "same-origin", // include, *same-origin, omit
        headers: {
            "Content-Type": "application/json",
            // "Content-Type": "application/x-www-form-urlencoded",
        },
        // redirect: "follow", // manual, *follow, error
        // referrer: "no-referrer", // no-referrer, *client
        body: JSON.stringify(data), // body data type must match "Content-Type" header
    })
    .then(response => response.json()); // parses response to JSON
}

const formSubmit = (e, form) => {
  try {
    e.preventDefault();
    const _form = document.getElementById('form');
    const data = {}
    const arr = Array.from(new FormData(_form), e => {
      e.map(encodeURIComponent)
      data[e[0]] = e[1];
      return { [e[0]]: e[1] }
    });

    const host = data.host;
    delete data.host;
    data.return_image = true
    postData(`${host}`, data)
    .then((d) => {
      if (d && d.base64) {
        const img = document.getElementById('result');
        img.src= `data:image/png;base64,${d.base64}`;
        const t = document.getElementById('time')
        t.innerText = `Speed: ${d.speed}`
        const jsonRes = document.getElementById('json');
        jsonRes.innerText = JSON.stringify({ objects: d.objects, image_size: d.image_size }, null, 2)
      }
    })
    .catch(e => {
      console.error('e', e)
    })

    return true;
  } catch (e) {
    console.error('e ', e);
    return true;
  }
}

setTimeout(() => {
  document.getElementById("host-field").value = `${window.location.protocol}//${window.location.host}/predict`;
}, 1000)
