const update_status = (history_url) => {
    fetch(history_url).then((res) => {
        if (res.ok) {
            res.json().then((res) => {
                res = JSON.parse(res)
                document.getElementById("now_playing").innerText = res.songs.pop().title

                document.getElementById("history").innerHTML = res.songs.reverse().map(song => {
                    return "<tr><td>" + song.last_played + "</td><td>" + song.title + "</td></tr>"
                }).join('')

                document.getElementById("listeners").innerText = res.listeners
            })
        }
    })
}