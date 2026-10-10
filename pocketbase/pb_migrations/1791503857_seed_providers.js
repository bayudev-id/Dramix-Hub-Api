/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("providers");
  if (!collection) return;

  const defaultProviders = [
    {
      "id": "rnq6kqauhc3y32z",
      "provider_id": "netshort",
      "name": "NetShort",
      "icon_url": "https://netshort.com/favicon.ico",
      "description": "Drama pendek sat-set dengan kategori jelajahi, rekomendasi, dubbing, dan VIP.",
      "content_type": "short_drama",
      "status": "active"
    },
    {
      "id": "78odtk5ocee0vi3",
      "provider_id": "melolo",
      "name": "Melolo",
      "icon_url": "https://play-lh.googleusercontent.com/HEkeCbNIuDdTlBr_2vuey1BeBTc-0O_RwemiQ80eWKGJFyJrq83Kk-34wOK_jqyXJ_XBP7eh3eoGg2nBbZd0eQ=s48-rw",
      "description": "Drama pendek vertikal dengan home kurasi, genre, dan episode multi-video.",
      "content_type": "short_drama",
      "status": "active"
    },
    {
      "id": "ft4ntqo3lndbs6e",
      "provider_id": "freereels",
      "name": "FreeReels",
      "icon_url": "https://play-lh.googleusercontent.com/1ybMEp7xw4kTY-K7ocih3vcbTEyCEqaxerVB6tDT8WcE3k5zCRR-jhKwS6Ct0UXIorczCIat3wTV0QLiuoLPdbY=s48-rw",
      "description": "Nonton video pendek dan film keren sepuasnya, gratis tis tis!",
      "content_type": "short_drama",
      "status": "active"
    },
    {
      "id": "yma91ahr232cy80",
      "provider_id": "moboreels",
      "name": "MoboReels",
      "icon_url": "https://dramahub.be/logos/moboreels.png",
      "description": "Koleksi drama pendek MoboReels yang siap ditonton kapan saja.",
      "content_type": "short_drama",
      "status": "active"
    },
    {
      "id": "24460kllftkp5rz",
      "provider_id": "shortwave",
      "name": "ShortWave",
      "icon_url": "https://dramahub.be/logos/shortwave.png",
      "description": "Koleksi drama pendek ShortWave yang siap ditonton kapan saja.",
      "content_type": "short_drama",
      "status": "active"
    },
    {
      "id": "unexytx3ms8bkf5",
      "provider_id": "dramaboxbaru",
      "name": "DramaBoxBaru",
      "icon_url": "https://dramahub.be/logos/dramaboxbaru.png",
      "description": "Koleksi drama pendek DramaBoxBaru yang siap ditonton kapan saja.",
      "content_type": "short_drama",
      "status": "inactive"
    },
    {
      "id": "1fec33akb8t8izp",
      "provider_id": "shortmax",
      "name": "ShortMax",
      "icon_url": "https://dramahub.be/logos/shortmax.png",
      "description": "Koleksi drama pendek ShortMax yang siap ditonton kapan saja.",
      "content_type": "short_drama",
      "status": "active"
    },
    {
      "id": "ez86e584wws5jya",
      "provider_id": "reelshort",
      "name": "ReelShort",
      "icon_url": "https://dramahub.be/logos/reelshort.png",
      "description": "Koleksi drama pendek ReelShort yang siap ditonton kapan saja.",
      "content_type": "short_drama",
      "status": "active"
    },
    {
      "id": "fekuik10c40f4c7",
      "provider_id": "stardusttv",
      "name": "StarDustTV",
      "icon_url": "https://dramahub.be/logos/stardusttv.png",
      "description": "Koleksi drama pendek StarDustTV yang siap ditonton kapan saja.",
      "content_type": "short_drama",
      "status": "active"
    },
    {
      "id": "lofqaq2fr4xliis",
      "provider_id": "dramarush",
      "name": "DramaRush",
      "icon_url": "https://dramahub.be/logos/dramarush.png",
      "description": "Koleksi drama pendek DramaRush yang siap ditonton kapan saja.",
      "content_type": "short_drama",
      "status": "active"
    },
    {
      "id": "yfk159mczo031en",
      "provider_id": "anichin",
      "name": "Anichin",
      "icon_url": "https://anichin.care/favicon-anichin.webp",
      "description": "Surga buat pecinta anime dan donghua, subtitle Indo.",
      "content_type": "movie_tv",
      "status": "active"
    },
    {
      "id": "dupctfntkf2r18n",
      "provider_id": "anichin2",
      "name": "Anichin V2",
      "icon_url": "https://anichin.care/favicon-anichin.webp",
      "description": "Donghua subtitle Indonesia langsung dari situs resmi anichin.moe.",
      "content_type": "movie_tv",
      "status": "active"
    },
    {
      "id": "p1bt56zg37l8fno",
      "provider_id": "samehadaku",
      "name": "Samehadaku",
      "icon_url": "https://v2.samehadaku.how/wp-content/uploads/2020/04/cropped-download-1-192x192.jpg",
      "description": "Anime subtitle Indonesia lengkap kualitas sampai 1080p.",
      "content_type": "movie_tv",
      "status": "active"
    },
    {
      "id": "kb3bbv5xrq5iv0x",
      "provider_id": "animelovers",
      "name": "Animelovers",
      "icon_url": "https://play-lh.googleusercontent.com/CLHjDsyke26uVVUlM14aRonR5cStB6VJEzxkhQhBb0Y_qVNQ7StMfeR8gD_o-yLvemLi_Ew8fXKBdpPkSuSgCA=w240-h480-rw",
      "description": "Nonton anime HD dengan speed kenceng.",
      "content_type": "movie_tv",
      "status": "active"
    },
    {
      "id": "u58ar2bsazqmhd5",
      "provider_id": "mobinime",
      "name": "Mobinime",
      "icon_url": "https://play-lh.googleusercontent.com/39_lxIoEMHNqjkx0tZiu8WzBcjTXO7KQyjP9lrDBqt5ij2oJEXfO8VZe9ulYp6c_ZK6UaQtGPrd3ovE2YELt=w240-h480-rw",
      "description": "Nonton anime lewat HP, cocok untuk wibu.",
      "content_type": "movie_tv",
      "status": "active"
    },
    {
      "id": "jz5e2andsm7dnac",
      "provider_id": "bstation",
      "name": "Bstation",
      "icon_url": "https://p.bstarstatic.com/fe-static/deps/bilibili_tv.ico?v=1",
      "description": "Konten kreatif dan anime kece.",
      "content_type": "movie_tv",
      "status": "active"
    },
    {
      "id": "yhnskefhjv07spi",
      "provider_id": "youku",
      "name": "Youku",
      "icon_url": "https://www.youku.tv/favicon.ico",
      "description": "Drama China eksklusif.",
      "content_type": "movie_tv",
      "status": "active"
    },
    {
      "id": "sm824o2w160jvgj",
      "provider_id": "CineMovies",
      "name": "CineMovies",
      "icon_url": "https://play-lh.googleusercontent.com/iGbFhJbNAz0ApocRri0Ak_dEi99oIXdb3RgeolnBp-l74Yq7rKYnMy2B02lU9V9RRkboGGcx7yQufjdSbTE3Rpo=w240-h480-rw",
      "description": "Solusi lengkap film dan serial TV.",
      "content_type": "movie_tv",
      "status": "active"
    },
    {
      "id": "3gyopkn1f46atrk",
      "provider_id": "CineTv",
      "name": "CineTv",
      "icon_url": "https://bittv.org/wp-content/uploads/2025/11/cropped-bit-tv-1-192x192.webp",
      "description": "Live TV dan channel tematik format Android terbaru.",
      "content_type": "live_tv",
      "status": "active"
    },
    {
      "id": "dr8d3zus5l1vr6f",
      "provider_id": "moviebox",
      "name": "MovieBox",
      "icon_url": "https://movieboxhd.net/favicon.ico",
      "description": "Drama dan Film Terlengkap",
      "content_type": "movie_tv",
      "status": "active"
    },
    {
      "id": "zm1xs35yfns5ti8",
      "provider_id": "kisskh",
      "name": "KissKH",
      "icon_url": "https://kisskh.do/assets/icons/icon-192x192.png",
      "description": "Drama dan Film Terlengkap",
      "content_type": "movie_tv",
      "status": "active"
    },
    {
      "id": "udzn6nqtv2c3kxk",
      "provider_id": "viu",
      "name": "VIU",
      "icon_url": "https://www.viu.com/ott/1viu-static/assets/favicon/favicon-96x96.png",
      "description": "Drama HD Terbaik dan Paling Ringan",
      "content_type": "movie_tv",
      "status": "active"
    },
    {
      "id": "zgfsiw94df422ar",
      "provider_id": "wetv",
      "name": "WeTV",
      "icon_url": "https://vfiles.wetvinfo.com/vupload/20200713/favicon.ico",
      "description": "Drama Long dan Short Terbaik",
      "content_type": "movie_tv",
      "status": "active"
    },
    {
      "id": "tbgq264ejnrj3k7",
      "provider_id": "iqiyi",
      "name": "iQIYI",
      "icon_url": "https://www.iq.com/favicon.ico",
      "description": "Drama Lengkap Pokoknya",
      "content_type": "movie_tv",
      "status": "active"
    }
  ];

  for (let i = 0; i < defaultProviders.length; i++) {
    const p = defaultProviders[i];
    try {
      const existing = app.findRecordsByFilter("providers", `provider_id = "${p.provider_id}"`, "", 1);
      if (existing && existing.length > 0) continue;
    } catch (e) {}

    const record = new Record(collection);
    record.set("id", p.id);
    record.set("provider_id", p.provider_id);
    record.set("name", p.name);
    record.set("icon_url", p.icon_url || "");
    record.set("description", p.description || "");
    record.set("content_type", p.content_type || "movie_tv");
    record.set("status", p.status || "active");
    app.save(record);
  }
}, (app) => {
  // Rollback intentionally empty
});
