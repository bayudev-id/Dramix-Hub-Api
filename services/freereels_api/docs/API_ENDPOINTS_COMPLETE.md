# FreeReels API Endpoints - Complete Map
## Extracted via JADX + Android-Reverse-IDE + Frida-Kahlo (2026-10-04)

> **Base URL:** `https://apiv2.free-reels.com`  
> **API Prefix:** `/frv2-api` (auto-prepended by `ApiPathInterceptor`)  
> **Auth Header:** `Authorization: oauth_signature={MD5(PREFIX+secret)},oauth_token={token},ts={timestamp_ms}`  
> **Exclusion:** `/anonymous/login` endpoint is excluded from Authorization header  
> **Secret Prefix:** `8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv&`

---

## 1. Authentication & User (y9.a)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/anonymous/login` | Guest/Anonymous login | ❌ No Auth |
| POST | `/user/login` | User login (Facebook/Google/Apple) | ✅ |
| POST | `/user/login/pre_check` | Pre-check login validity | ✅ |
| POST | `/user/logout` | Logout | ✅ |
| POST | `/user/logoff` | Delete account | ✅ |
| POST | `/user/reel_user_transfer` | Transfer user data | ✅ |
| GET | `/user/risk/check` | Check deactivation risk | ✅ |
| GET | `/user/setting/config` | User settings configuration | ✅ |
| GET | `/user/short_token` | Get short-lived token | ✅ |
| GET | `/welfare/v2/guide-login` | Guide login welfare | ✅ |
| GET | `/content/message/unread` | Unread message count | ✅ |
| POST | `/risk/yidun/check` | Risk detection check | ✅ |

## 2. User Profile (y9.p)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/user/profilev2` | Get user profile | ✅ |
| POST | `/user/edit` | Edit profile | ✅ |
| GET | `/user/age` | Get/set age | ✅ |
| GET | `/user/upload/url` | Get avatar upload URL | ✅ |
| GET | `/user/device/list` | List devices | ✅ |
| POST | `/user/device/logout` | Logout device | ✅ |
| GET | `/user/profile/func` | Profile settings sort | ✅ |
| GET | `/user/net-check/conf` | Network check config | ✅ |
| GET | `/my/preference/get` | Get preferences | ✅ |
| POST | `/my/preference/save` | Save preferences | ✅ |
| GET | `/my/preference/popup/config` | Preference popup config | ✅ |
| POST | `/my/preference/popup/submit` | Submit popup preference | ✅ |

## 3. Wallet & VIP (y9.p)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/wallet/my` | My wallet info | ✅ |
| GET | `/wallet/sku/list` | SKU list (IAP items) | ✅ |
| GET | `/wallet/product/list` | Product list for purchase | ✅ |
| GET | `/wallet/vip/center_v2` | VIP center page | ✅ |
| GET | `/wallet/vip/benefits` | VIP benefits info | ✅ |
| POST | `/wallet/autounlock/change` | Change auto-unlock | ✅ |
| POST | `/wallet/subscription/guide/page` | Subscription guide | ✅ |
| POST | `/wallet/subscription/landing/page` | Subscription landing | ✅ |
| POST | `/wallet/subscription/landing/report` | Report subscription landing | ✅ |
| POST | `/wallet/subscription/landing/remind` | Subscription reminder | ✅ |
| GET | `/wallet/subscription/landing/is-target-user` | Is target user for sub | ✅ |

## 4. Homepage & Feed (y9.b, y9.f, y9.j, Frida Live)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/homepage/v2/tab/index` | **Main feed** (params: tab_key, position_index, rec_trigger) | ✅ |
| GET | `/homepage/user_latest_view_series` | Last viewed series | ✅ |
| POST | `/homepage/rank` | Ranking list | ✅ |
| GET | `/homepage/rank/actor/list` | Actor ranking list | ✅ |
| POST | `/homepage/rank/actor/info` | Actor rank info | ✅ |
| POST | `/homepage/rank/actor/vote` | Vote for actor | ✅ |
| POST | `/homepage/rank/actor/voting/info` | Actor voting info | ✅ |
| POST | `/homepage/resource/filter` | Category filter | ✅ |
| POST | `/homepage/feed-insert` | Feed insert | ✅ |
| POST | `/homepage/newuser/strategy` | New user strategy | ✅ |

## 5. Drama & Episodes (y9.i)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/drama/info_v2` | **Drama detail** (series_id, scene, clip_content, campaign) | ✅ |
| GET | `/drama/info_push_v2` | Drama info push variant | ✅ |
| GET | `/drama/price` | Episode pricing | ✅ |
| GET | `/drama/download` | Download episode (returns HLS URL) | ✅ |
| GET | `/drama/v2/download` | Download v2 | ✅ |
| POST | `/drama/unlock_episode` | **Unlock single episode** | ✅ |
| POST | `/drama/batch_unlock_episode` | Unlock multiple episodes | ✅ |
| GET | `/drama/multi_unlock/price` | Multi-unlock pricing | ✅ |
| GET | `/drama/unlock_tag` | Unlock tag | ✅ |
| GET | `/drama/label` | Drama labels/tags | ✅ |
| POST | `/drama/follow` | Follow a drama | ✅ |
| POST | `/drama/view` | Report view (tracking) | ✅ |
| POST | `/drama/view_time` | Report view time | ✅ |
| POST | `/drama/episode/like` | Like episode | ✅ |
| GET | `/drama/episode/like/list` | Liked episodes list | ✅ |
| POST | `/drama/episode/like/batch-cancel` | Batch cancel likes | ✅ |
| GET | `/drama/completion/popup` | Completion popup | ✅ |
| POST | `/drama/v2/download/change_benefit` | Change download benefit | ✅ |
| POST | `/play/quit/retention` | Quit/retention tracking | ✅ |
| POST | `/play/pick_for_you` | Personalized recommendations | ✅ |

## 6. My List & Library (y9.l)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/drama/v3/follow_list` | Following list | ✅ |
| GET | `/drama/v3/follow_list_fallback` | Following list fallback | ✅ |
| GET | `/drama/v3/view_history` | View history | ✅ |
| GET | `/drama/book-list` | Bookmarked list | ✅ |
| POST | `drama/batch_delete_history_v2` | Delete history (batch) | ✅ |
| POST | `/drama/batch_unfollow_v2` | Unfollow batch | ✅ |
| POST | `drama/batch-unbook` | Unbookmark batch | ✅ |

## 7. For You Feed (y9.i)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/foryou/feed` | For You personalized feed | ✅ |
| POST | `/foryou/open-series` | Open series from For You | ✅ |

## 8. Free Soon (y9.h)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/freesoon/index` | Free Soon index | ✅ |
| POST | `/freesoon/feed` | Free Soon feed | ✅ |
| POST | `/freesoon/item/list` | Free Soon item list | ✅ |
| POST | `/freesoon/unlock-left` | Unlock left count | ✅ |

## 9. Comments & Barrage (y9.g)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/content/comment/list` | Comment list | ✅ |
| POST | `/content/comment/sub_list` | Sub-comment list | ✅ |
| POST | `/content/comment/save` | Post comment | ✅ |
| POST | `/content/comment/like` | Like comment | ✅ |
| POST | `/content/comment/dislike` | Dislike comment | ✅ |
| POST | `/content/comment/delete` | Delete comment | ✅ |
| POST | `/content/comment/data` | Comment data/count | ✅ |
| GET | `/content/comment/activity` | Comment activity | ✅ |
| GET | `/content/comment/image/upload-url` | Upload image URL | ✅ |
| POST | `/content/comment/sticker/list` | Sticker list | ✅ |
| POST | `/content/comment/sticker/add` | Add sticker | ✅ |
| POST | `/content/comment/sticker/delete` | Delete sticker | ✅ |
| POST | `/content/barrage/open_status/switch` | Danmaku toggle | ✅ |
| POST | `/content/barrage/show` | Show danmaku | ✅ |

## 10. Messages (y9.p)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/content/message/unread` | Unread messages | ✅ |
| GET | `/content/message/list` | Message list | ✅ |
| POST | `/content/message/mark` | Mark message read | ✅ |
| GET | `/content/message/read-all` | Read all messages | ✅ |

## 11. Welfare & Rewards (y9.e)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/welfare/v2/list/new` | Reward task list | ✅ |
| GET | `/welfare/v2/sign` | Check-in / sign | ✅ |
| POST | `/welfare/v2/receive` | Receive reward | ✅ |
| POST | `/welfare/v2/ad-receive` | Receive ad reward | ✅ |
| POST | `/welfare/v2/finish` | Finish task | ✅ |
| GET | `/welfare/v2/wallet` | Welfare wallet | ✅ |
| GET | `/welfare/v2/treasure-chest` | Treasure chest | ✅ |
| GET | `/welfare/v2/treasure-pendant` | Treasure pendant | ✅ |
| GET | `/welfare/v2/new_user/detail` | Newbie welfare | ✅ |
| GET | `/welfare/v2/client-exp` | Client experiment | ✅ |
| POST | `/welfare/v2/download/precheck` | Download precheck | ✅ |
| POST | `/welfare/v2/receive-reward-options` | Reward options | ✅ |
| POST | `/welfare/v2/watch-video-report` | Watch video report | ✅ |
| GET | `/welfare/v2/claimable-task-popup` | Claimable task popup | ✅ |
| POST | `/welfare/v2/withdraw_red_package/alert/show` | Withdraw alert | ✅ |
| POST | `/welfare/v2/shop/exchange` | Shop exchange | ✅ |
| GET | `/welfare/v2/withdrawal/past` | Withdrawal history | ✅ |
| GET | `/welfare/v2/reward_ele/show` | Reward element show | ✅ |
| GET | `/frv2-api/welfare/v2/reward_popup/show` | Reward popup | ✅ |
| GET | `/frv2-api/welfare/v2/global-pendant` | Global pendant | ✅ |
| POST | `/frv2-api/welfare/v2/viral-popup` | Viral popup | ✅ |
| GET | `welfare/v2/viral-icon` | Viral icon | ✅ |

## 12. Ads (y9.i)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/ad/get` | Get ad config | ✅ |
| POST | `/ad/finish` | Report ad completion | ✅ |
| POST | `/advertise/series/resolve` | Resolve advertised series | ✅ |
| GET | `/advertise/content-info` | DDL content info | ✅ |
| GET | `/frv2-api/free-ad/start` | Free ad start | ✅ |
| GET | `/frv2-api/free-ad/conf` | Free ad config | ✅ |
| GET | `/frv2-api/free-ad/status` | Free ad status | ✅ |

## 13. Viral & Sharing (y9.e)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/l/create` | Create short URL | ✅ |
| GET | `/viral/share-plugin-order` | Share plugin order | ✅ |
| GET | `/viral/bind-code` | Bind referral code | ✅ |

## 14. System / Config (y9.d)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/sys/config` | System config | ✅ |
| GET | `/app/config` | App config | ✅ |
| GET | `/app/abtest/hits` | A/B test hits | ✅ |
| POST | `/sys/version/latest` | Check app update | ✅ |
| POST | `/user/setting/language` | Set language | ✅ |
| GET | `/float/info` | Float config | ✅ |
| POST | `/push/guide-user-open-push` | Push notification guide | ✅ |

## 15. Tickets / Coupons (y9.p)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/ticket/list` | Digital ticket list | ✅ |
| GET | `/ticket/is_show` | Show ticket | ✅ |
| POST | `/ticket/create` | Create ticket | ✅ |
| GET | `/coupon/list` | Coupon list | ✅ |

## 16. User Block (y9.g)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/user/block` | Block user | ✅ |

## 17. Device Management (y9.k)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/user/device/remove_others` | Remove other devices | ✅ |
| GET | `/reward/pendant/show` | Reward pendant | ✅ |
| POST | `/reward/pendant/close` | Close pendant | ✅ |

## 18. Risk / Anti-Fraud

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/kocr/user-auth/check` | KOCR auth check | ✅ |
| POST | `/kocr/user-auth/start` | KOCR auth start | ✅ |
| GET | `/user/ascribe/status` | Ascribe status | ✅ |

## 19. Tracking / Analytics

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `https://trace.free-reels.com/b/frv2_client_track` | Client tracking events | ✅ |
| POST | `https://apiv2.free-reels.com/frv2-api/risk/sm/proxy` | ShumeiAntifraud proxy | ✅ |

---

## Tab Keys (From Frida Live Capture)

| Tab Key | Name |
|---------|------|
| `503` | Popular |
| `505` | New Released |
| `547` | Anime |

## Live Credentials (Captured via Frida)

```
oauth_token  = xYMHaotTuCSkAG43RTvrryiEThdntAdB
oauth_secret = fnb4RGMj8HrjOOiB4OUOk8FYln7bEF2k
user_id      = 26328508671
name         = Guest
app_version  = 2.4.91
device_id    = da9ce769379941e4
```

## Important Notes

1. **App Version Updated**: APK is `2.4.91` (not `2.2.00` as previously noted)
2. **ApiPathInterceptor** auto-prepends `/frv2-api` to all paths, except those that already start with `/frv2-api`
3. **`/anonymous/login`** is the ONLY endpoint excluded from `Authorization` header
4. **Signature:** `MD5("8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv&" + oauth_secret)`
5. **Header Format:** `oauth_signature={sig},oauth_token={token},ts={ms_timestamp}`
6. **CDN Hosts**: `static-v1.mydramawave.com` (images), `video-v*.mydramawave.com` (video)
7. **Alternative API Host**: `api-100.free-reels.com` (seen in Frida SSL bypass log)
8. **Network Stack**: Uses `libsscronet.so` (Cronet-based) which explains why traffic bypasses system proxy (Burp Suite)
