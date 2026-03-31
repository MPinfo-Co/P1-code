export const mockKnowledge = {
  1: {
    摘要: `【事件等級】★★★★★ 最高危\n【威脅類型】APT 進階持續性威脅 — DNS C2 Tunneling + Beaconing\n【核心發現】內部主要 DNS 伺服器 192.168.10.20 已遭植入惡意程式，利用 DNS 協定作為 C2（指令與控制）通道與 180.76.76.95（Baidu DNS）等 258 個外部 IP 維持心跳連線。10 小時內偵測 595 筆異常查詢，封包大小（89-112 B）符合加密 Beaconing 特徵。\n【影響評估】DNS 伺服器若已淪陷，攻擊者可對整個內網進行 DNS Hijacking、內部資產探測、側向移動。此為完整 APT Kill Chain 的持久化階段。`,
    發現: `【IOC 清單】\n‣ 來源 IP：192.168.10.20（內部 DNS Server — 已淪陷）\n‣ 目的 IP：180.76.76.95（Baidu DNS，已知 C2 中繼）+ 258 個分散外部 IP\n‣ 封包特徵：sentbyte 89-112 B，Fast-flux 行為，查詢頻率 595 次/10h\n‣ 通訊協定：UDP 53（DNS）\n【MITRE ATT&CK 對應】\n‣ T1071.004 — Application Layer Protocol: DNS（C2 通訊）\n‣ T1568.001 — Dynamic Resolution: Fast Flux DNS（規避偵測）\n‣ T1041 — Exfiltration Over C2 Channel（可能的資料外洩通道）`,
    說明: `DNS Tunneling 攻擊利用 DNS 查詢封包夾帶任意資料，因 DNS 流量通常被防火牆放行而難以攔截。攻擊者在受害主機植入 Agent 後，透過 DNS TXT/CNAME 記錄型別傳輸加密 C2 指令，每次查詢僅攜帶少量資料（<200 B）刻意繞過異常流量告警。Fast-flux 技術則透過頻繁切換 DNS 解析目標 IP，使封鎖單一 IP 的防禦策略失效。`,
    修復: `【立即行動 — 0~4 小時】\n1. 立即隔離 192.168.10.20（從網路切斷，保留記憶體映像供鑑識）\n   config firewall policy\n     edit 0\n       set srcaddr "192.168.10.20"\n       set action deny\n       set logtraffic all\n     next\n   end\n2. 備用 DNS 切換：將所有 DHCP/靜態設定指向備用 DNS（如 8.8.8.8）\n3. 封鎖 180.76.76.95 及相關 C2 IP 段\n\n【中期處置 — 4~24 小時】\n4. 對 192.168.10.20 進行完整記憶體鑑識（Volatility 3）與磁碟 Imaging\n5. 重建乾淨的 DNS Server（全新安裝，勿還原可能感染的備份）\n6. 在 Fortigate 啟用 DNS Filter，過濾惡意 Domain 清單（Threat Feed）\n7. 審查近 30 天所有 DNS 查詢日誌，找出 Fast-flux 特徵的其他內部主機\n\n【長期強化】\n8. 部署 DNS over HTTPS（DoH）監控或 RPZ（Response Policy Zone）\n9. 設定 DNS 查詢頻率基線告警（單一主機 >50 次/小時對外 DNS 即告警）`,
    步驟前綴: {
      0: `【Fortigate 防火牆隔離操作】\n\n執行環境：Fortigate CLI（SSH 連線）\n\n步驟 1：確認目前策略 ID\n  show firewall policy | grep -A5 "192.168.10.20"\n\n步驟 2：建立封鎖策略（優先序置頂）\n  config firewall policy\n    edit 0\n      set name "ISOLATE-DNS-SERVER-192.168.10.20"\n      set srcintf "internal"\n      set dstintf "wan1"\n      set srcaddr "192.168.10.20"\n      set dstaddr "all"\n      set action deny\n      set schedule "always"\n      set logtraffic all\n      set comments "APT C2 隔離 - 2026-02-23 緊急"\n    next\n  end\n\n步驟 3：驗證策略生效\n  diagnose firewall iprobe show 100004\n  execute ping 180.76.76.95 source 192.168.10.20  # 應超時\n\n步驟 4：持續監控封鎖日誌\n  execute log display | grep 192.168.10.20`,
    },
  },
  2: {
    摘要: `【事件等級】★★★★☆ 高危\n【威脅類型】防火牆策略錯誤配置 — 任意出站流量允許\n【核心發現】SVR_to_WAN 策略允許伺服器區段的主機（192.168.10.0/24）對任意外部目的地發出任意協定流量，10 小時內產生 135,542 筆出站連線，平均每秒 3.76 筆。此配置嚴重違反最小權限原則，一旦任一伺服器遭入侵，攻擊者可無障礙地對外建立 C2 通道。\n【影響評估】目前已有 Issue #1（DNS C2）利用此寬鬆策略成功維持通訊，意味此配置缺口是整起事件的基礎架構根因。`,
    發現: `【問題配置詳情】\n‣ 策略名稱：SVR_to_WAN\n‣ 來源：internal_servers（192.168.10.0/24）\n‣ 目的：any（全部外部 IP）\n‣ 服務：any（全部協定/Port）\n‣ 動作：accept\n‣ 實際流量：135,542 筆 / 10 小時，目的地涵蓋 892 個不同外部 IP\n【高風險連線發現】\n‣ 192.168.10.20 → 180.76.76.95（已知 C2，即 Issue #1）\n‣ 192.168.10.x → 多個中國/荷蘭 IP（GeoIP 高風險地區）\n‣ 非標準 Port 連線：多筆 TCP 443 以外的加密通道嘗試`,
    說明: `「任意出站（Any to Any）」策略是企業防火牆最常見的嚴重配置錯誤之一。此類策略通常在初期為方便性而設置，但長期未收緊，導致攻擊面極度擴大。攻擊者一旦在伺服器區段取得立足點，可利用任意協定（HTTP/HTTPS/DNS/ICMP）建立隱蔽 C2 通道，傳統防火牆因未做內容檢測而無法識別。`,
    修復: `【立即行動】\n1. 盤點 SVR_to_WAN 策略下所有伺服器的合法出站需求（業務白名單）\n   execute log filter category 1\n   execute log filter field srcip 192.168.10.0/24\n   execute log display\n\n2. 逐步收緊策略（分三階段避免業務中斷）：\n   config firewall policy\n     edit <SVR_to_WAN策略ID>\n       set dstaddr <業務白名單地址群組>\n       set service HTTPS HTTP DNS NTP SMTP\n     next\n   end\n\n3. 立即套用 GeoIP 封鎖（中國/俄羅斯/北韓/伊朗）：\n   config firewall policy\n     edit 0\n       set name "GEOIP-BLOCK-HIGH-RISK"\n       set srcaddr "all"\n       set dstaddr "CHINA-IP RUSSIA-IP"\n       set action deny\n       set logtraffic all\n     next\n   end\n\n4. 啟用 Application Control + IPS Profile 附掛於 SVR_to_WAN 策略`,
    步驟前綴: {
      0: `【防火牆策略收緊操作 — Fortigate CLI】\n\n步驟 1：查詢目前 SVR_to_WAN 策略 ID\n  show firewall policy | grep -B2 -A20 "SVR_to_WAN"\n\n步驟 2：建立伺服器合法出站白名單群組\n  config firewall addrgrp\n    edit "SVR-ALLOWED-DST"\n      set member "UPDATE-SERVERS" "NTP-SERVERS" "SMTP-RELAY"\n    next\n  end\n\n步驟 3：修改策略限制目的地\n  config firewall policy\n    edit <ID>\n      set dstaddr "SVR-ALLOWED-DST"\n      set service "HTTPS" "HTTP" "DNS" "NTP"\n    next\n  end\n\n步驟 4：建立 GeoIP 封鎖政策\n  config firewall policy\n    edit 0\n      set name "BLOCK-HIGH-RISK-GEOIP"\n      set srcaddr "all"\n      set dstaddr "China Russia NorthKorea Iran"\n      set action deny\n      set schedule "always"\n      set logtraffic all\n    next\n  end`,
    },
  },
  3: {
    摘要: `【事件等級】★★★☆☆ 中危\n【威脅類型】VPN 用戶端異常 DNS 回應 — 潛在 DNS Payload 注入\n【核心發現】VPN 用戶端 172.18.1.62 收到來自 DNS 伺服器的超大 DNS 回應封包（rcvbyte 2,341 B），遠超正常 DNS 回應大小（通常 <512 B）。與 Issue #1 的 DNS C2 事件時間重疊。\n【影響評估】異常大 DNS 回應可能為夾帶 Payload 的 DNS Tunneling 下行指令包，需立即進行 PCAP 鑑識分析。`,
    發現: `【IOC 清單】\n‣ 受害端：172.18.1.62（VPN 用戶端，身份待確認）\n‣ 異常 DNS 回應大小：2,341 B（正常基線：<512 B）\n‣ 觸發時間：13:29:51（與 DNS C2 事件同日）\n‣ 封包數量：2 筆（小數量但大封包，Low-and-Slow 特徵）\n【關聯分析】\n‣ 此端點可能是 Issue #1 DNS C2 攻擊鏈的下游受害者\n‣ VPN 環境下的端點鑑識困難，需要端點代理（EDR）協助\n‣ 需確認 172.18.1.62 的 VPN 使用者身份`,
    說明: `正常 DNS UDP 回應封包不超過 512 B（RFC 1035 限制），使用 EDNS0 擴充後也多在 1,232 B 以下。當回應封包達到 2,000+ B 時，最可能的情境為 DNS Tunneling 的下行 Payload 夾帶（攻擊者透過 TXT 記錄夾帶 Base64 指令）。綜合本案時間脈絡與 Issue #1 的關聯，威脅可能性極高。`,
    修復: `【立即行動】\n1. 確認 172.18.1.62 的 VPN 使用者身份（查詢 VPN 連線日誌）\n   execute log filter field remip 172.18.1.62\n   execute log filter category 7\n   execute log display\n\n2. 強制該 VPN 使用者重新認證並要求端點掃描\n3. 擷取 PCAP 進行人工分析：\n   diagnose sniffer packet any "host 172.18.1.62 and port 53" 6 100 l\n4. 在 DNS 層啟用 DNS Response Size 限制（>800 B 即告警）\n5. 若確認為 Tunneling 受害端，立即隔離該端點並進行 EDR 鑑識`,
    步驟前綴: {
      0: `【PCAP 擷取與分析步驟】\n\n步驟 1：在 FortiGate 上擷取針對 172.18.1.62 的 DNS 流量\n  diagnose sniffer packet any "host 172.18.1.62 and port 53" 6 500 l\n\n步驟 2：將 PCAP 匯出並用 Wireshark 分析\n  dns.resp.len > 800\n  dns.qry.type == 16  # TXT 記錄（常用於 Tunneling）\n\n步驟 3：識別 DNS Tunneling 特徵\n  - DNS TXT 記錄是否含有 Base64 字串\n  - 查詢的 Domain 是否為隨機長字串（entropy > 3.5）\n  - 是否有規律的時間間隔（Beaconing pattern）\n\n步驟 4：使用 dnscat2 / iodine 特徵比對\n  strings pcap_file.pcap | grep -E "[A-Za-z0-9+/]{50,}=*"\n\n步驟 5：確認後立即封鎖來源 DNS 伺服器 IP 並隔離端點`,
    },
  },
  4: {
    摘要: `【事件等級】★★☆☆☆ 低危（監測中）\n【威脅類型】分散式低速暴力破解（Low-and-Slow Distributed Brute Force）\n【核心發現】多個外部來源 IP 對行政帳號（EventID 4625）進行分散式暴力破解攻擊，10 小時內偵測 2,847 筆失敗登入，攻擊者採用多 IP 輪換策略刻意繞過傳統帳號鎖定機制。Windows Security Event Log 已記錄完整攻擊序列。\n【影響評估】若行政帳號密碼強度不足，攻擊者可能已在監測期間外完成入侵。需立即查看是否有對應的成功登入（EventID 4624）事件。`,
    發現: `【IOC 清單】\n‣ 攻擊目標：Administrator 及 mp0391 帳號\n‣ EventID 4625：2,847 筆失敗登入 / 10 小時\n‣ 攻擊 IP 數量：多個（分散式，每 IP < 50 次以規避鎖定）\n‣ 攻擊來源：Netherlands、Bulgaria\n【需要確認的事項】\n‣ 是否有對應的 EventID 4624（成功登入）？\n‣ 是否有 EventID 4648（明確認證嘗試）？\n‣ 攻擊來源是否與已知 Botnet 清單相符？`,
    說明: `傳統暴力破解每個 IP 高頻嘗試，會觸發帳號鎖定（通常 5 次失敗）。進化版的 Low-and-Slow 攻擊使用 Botnet 或代理池，每個 IP 僅嘗試 2-3 次（低於鎖定閾值），但跨越數十到數百個 IP 累積大量嘗試。此攻擊在日誌量大的環境中容易被淹沒，需要特殊的異常行為分析（UEBA）來識別。`,
    修復: `【立即行動 — 0~4 小時】\n1. 查詢是否有成功登入（最高優先）：\n   Get-WinEvent -LogName Security -FilterXPath "*[System[EventID=4624]...]" | Select TimeCreated, Message\n\n2. 立即對所有行政帳號強制重設密碼（複雜度 16 字元以上）\n\n3. 在 Fortigate 封鎖攻擊來源 IP 段：\n   config firewall policy\n     edit 0\n       set name "BLOCK-BRUTEFORCE-SRC"\n       set srcaddr <攻擊IP群組>\n       set dstaddr "ADMIN-SERVERS"\n       set action deny\n     next\n   end\n\n4. 啟用 MFA（多因素驗證）— 對所有行政帳號強制執行\n\n5. 調高帳號鎖定閾值策略（降低鎖定閾值至 3 次）`,
    步驟前綴: {
      0: `【Windows Security Log 分析步驟】\n\n步驟 1：匯出 EventID 4625 清單並整理攻擊 IP\n  $events = Get-WinEvent -LogName Security | Where-Object {$_.Id -eq 4625}\n  $events | ForEach-Object {\n    $xml = [xml]$_.ToXml()\n    $ip = $xml.Event.EventData.Data | Where-Object {$_.Name -eq 'IpAddress'} | Select-Object -Expand '#text'\n    [PSCustomObject]@{Time=$_.TimeCreated; IP=$ip}\n  } | Sort-Object IP | Export-Csv brute_force.csv -Encoding UTF8\n\n步驟 2：統計各 IP 嘗試次數\n  Import-Csv brute_force.csv | Group-Object IP | Sort-Object Count -Descending | Select -First 20\n\n步驟 3：交叉比對成功登入\n  Get-WinEvent -LogName Security | Where-Object {$_.Id -eq 4624 -and $_.TimeCreated -gt (Get-Date).AddDays(-1)}\n\n步驟 4：若發現成功入侵，立即執行\n  net user Administrator /active:no`,
    },
  },
  5: {
    摘要: `【事件等級】★★☆☆☆ 低危（追蹤觀察）\n【威脅類型】VPN 用戶端異常封包大小（可能為誤報）\n【核心發現】VPN 用戶端 172.18.1.61 產生 2 筆 DNS 相關流量，封包大小介於 556-1,270 B，略超正常 DNS 上限。但頻率極低，且發生時間點與 Issue #3 的 172.18.1.62 不同，目前評估為低優先追蹤事件，誤報可能性約 60%。\n【影響評估】單獨來看風險低，但若與 Issue #1、#3 的 DNS 異常模式相關，則可能是更大範圍入侵的一部分。`,
    發現: `【觀察到的異常】\n‣ 端點：172.18.1.61（與 172.18.1.62 為相鄰 VPN 位址段）\n‣ 異常封包：最大 1,270 B\n‣ 協定：DNS（UDP 53）\n‣ 頻率：極低（2 次 / 10 小時）\n【誤報可能性評估】\n‣ 某些正常 DNS 擴充（EDNS0 + DNSSEC 簽名）可能導致封包接近 1,200 B\n‣ 頻率遠低於 Issue #3 的 2 筆（且 #3 封包更大）\n‣ 建議與 DNS Server 日誌交叉比對確認`,
    說明: `此事件目前屬於「統計異常」而非「確認威脅」。現代 DNS 協定已廣泛使用 EDNS0（Extension Mechanisms for DNS）擴充，允許封包超過傳統 512 B 限制。DNSSEC 簽名、IPv6 記錄（AAAA）以及 SRV 記錄等也可能產生較大封包。在評估是否為真實威脅時，頻率、模式的規律性、以及與已知 C2 IP 的關聯性比封包大小本身更重要。`,
    修復: `【建議處置（低優先）】\n1. 將此事件列入持續觀察清單，設定 7 天追蹤期\n2. 查詢 172.18.1.61 的 VPN 使用者身份，確認為正常業務使用者\n3. 若 Issue #1 DNS C2 確認為真實攻擊，升高此事件優先序至「高危」\n4. 設定自動告警：若 172.18.1.61 的 DNS 流量頻率增加 > 10 倍，立即通知\n\n【驗證為誤報的方式】\n  nslookup -type=ANY <查詢的Domain> <DNS_Server_IP>\n  # 若結果含 DNSSEC 或大量 TXT 記錄，則為正常`,
    步驟前綴: {
      0: `【觀察清單建立步驟】\n\n步驟 1：確認 172.18.1.61 的使用者身份\n  execute log filter field remip 172.18.1.61\n  execute log filter category 7\n  execute log display\n\n步驟 2：建立持續監控規則（FortiGate）\n  config log fortianalyzer filter\n    edit 0\n      set srcip 172.18.1.61\n      set severity information\n    next\n  end\n\n步驟 3：7 天後重新評估（若無新告警則標記為誤報關閉）`,
    },
  },
  6: {
    摘要: `【事件等級】★☆☆☆☆ 環境雜訊（正常防禦運作）\n【威脅類型】外部高風險地理來源連線攔截 — 防火牆正常工作\n【核心發現】Fortigate 防火牆在 10 小時內自動攔截 1,735,168 筆來自高風險地理區域的入站連線嘗試，此屬正常 GeoIP 封鎖策略的日常防禦量，無需特別處置。\n【影響評估】此為訊息性事件（Informational）。大量攔截本身是好事，代表防禦機制正常運作。`,
    發現: `【統計資料】\n‣ 攔截總量：1,735,168 筆 / 10 小時（平均 173,517 筆/小時）\n‣ 主要來源地區：中國大陸（約 65%）、東南亞（約 20%）、俄羅斯（約 10%）、其他（5%）\n‣ 主要攻擊類型：Port Scanning（80%）、暴力破解嘗試（15%）、漏洞探測（5%）\n【基線比較建議】\n‣ 需要建立 30 天的封鎖量基線才能判斷今日是否異常\n‣ 若今日量是過去均值的 3 倍以上，建議升高警戒`,
    說明: `每日 100~200 萬筆的 GeoIP 封鎖量對有對外 IP 的企業而言屬於正常範圍。全球每天有數百萬個自動化掃描器（Shodan、Censys、Botnet 等）持續對所有公開 IP 進行探測。GeoIP 封鎖雖有效降低攻擊面，但並非萬能——需注意 VPN 繞過以及誤封合法流量（如海外出差員工）的情況。`,
    修復: `【維運建議（非緊急）】\n1. 建立封鎖量每日基線報表（以 FortiAnalyzer 或 SIEM 匯整）\n2. 確認 GeoIP 封鎖清單每季更新（IP 地理位置資料會變動）\n3. 設定封鎖量突增告警（超過均值 200% 即通知）\n4. 評估是否需要將海外合法存取 IP 加入白名單\n5. 確認 Port 443/80/22/3389 等常見攻擊面的 GeoIP 封鎖有完整覆蓋`,
    步驟前綴: {
      0: `【GeoIP 封鎖基線報表設定】\n\n步驟 1：FortiGate 匯出封鎖統計\n  execute log filter category 1\n  execute log filter field action deny\n  execute log display\n\n步驟 2：設定每日定時報表（FortiAnalyzer）\n  Reports → Report Definitions → New Report\n  Name: Daily-GeoIP-Block-Summary\n  Schedule: Daily 23:55\n\n步驟 3：建立告警規則（封鎖量 > 3倍基線即傳送 Email 告警）\n  config alertemail setting\n    set username "admin@company.com"\n    set mailto "soc@company.com"\n  end`,
    },
  },
}

export const similarCasesData = {
  1: [
    {
      id: 'SC001',
      date: '2025-11-15',
      title: 'DNS Tunneling 感染事件',
      similarity: 92,
      summary:
        '內部 DNS 伺服器 192.168.10.15 向中國 IP 持續發出異常 DNS 查詢（Fast-flux 特徵），確認為 dnscat2 工具感染，C2 Beaconing 行為。',
      outcome: '已完成',
      resolvedAt: '2025-11-15 14:32',
      resolvedBy: 'Rex Shen',
      resolution:
        '隔離主機、重新安裝 OS，更新防火牆 GeoIP 規則封鎖中國及荷蘭 IP，加強 DNS 解析行為監控。',
    },
    {
      id: 'SC002',
      date: '2025-08-03',
      title: '郵件伺服器 C2 Beaconing 偵測',
      similarity: 74,
      summary: '郵件伺服器定期向外部 IP 發出心跳包，傳輸長度異常（87-115 B），確認為惡意後門程式。',
      outcome: '已完成',
      resolvedAt: '2025-08-03 09:15',
      resolvedBy: 'Dama Wang',
      resolution: '移除惡意後門程式、強化出站流量告警，部署 NDR 側錄規則。',
    },
  ],
  2: [
    {
      id: 'SC003',
      date: '2025-06-20',
      title: 'SVR_to_WAN 防火牆策略過寬',
      similarity: 88,
      summary:
        '多條防火牆規則允許伺服器段任意對外連線，經稽核發現有 5 台主機利用此策略進行未授權的外部通訊。',
      outcome: '已完成',
      resolvedAt: '2025-06-20 16:50',
      resolvedBy: 'Frank Liu',
      resolution: '建立目的地白名單、啟用 GeoIP 過濾，策略調整後減少 73% 不必要流量。',
    },
  ],
  3: [
    {
      id: 'SC004',
      date: '2025-09-12',
      title: 'VPN 用戶端 DNS Payload 注入',
      similarity: 91,
      summary:
        'VPN 用戶端收到超大型 DNS 回應（3.1 KB），分析確認為攻擊者使用 iodine 工具進行橫向移動嘗試。',
      outcome: '已完成',
      resolvedAt: '2025-09-12 11:20',
      resolvedBy: 'Rex Shen',
      resolution: 'PCAP 分析確認為惡意 payload、強制 DNS 快取清理、端點掃描確認未進一步感染。',
    },
    {
      id: 'SC005',
      date: '2025-12-01',
      title: 'VPN 異常封包監測（誤報）',
      similarity: 62,
      summary: 'VPN 段多台設備收到異常大型封包，後確認為 EDNS0 合法 TXT 記錄查詢。',
      outcome: '擱置',
      resolvedAt: '2025-12-01 08:45',
      resolvedBy: 'Dama Wang',
      resolution: '確認為誤報，建立流量閾值 > 2 KB 才觸發高優先告警，降低 SOC 分析負荷。',
    },
  ],
  4: [
    {
      id: 'SC006',
      date: '2026-01-08',
      title: '行政帳號 Low-and-Slow 暴力破解',
      similarity: 95,
      summary:
        'Administrator 帳號遭受來自東歐多個 IP 的低速暴力破解（每分鐘 < 3 次嘗試，持續 48 小時）以規避鎖定偵測。',
      outcome: '已完成',
      resolvedAt: '2026-01-08 22:10',
      resolvedBy: 'Rex Shen',
      resolution: '啟用 MFA、Fortinet IPS 封鎖來源 IP 段、稽核近 30 天成功登入紀錄確認無入侵。',
    },
  ],
  5: [
    {
      id: 'SC007',
      date: '2025-09-12',
      title: 'VPN DNS 1.1 KB 異常回應（同期）',
      similarity: 83,
      summary:
        'VPN 用戶端 172.18.1.55 收到 1.1 KB DNS 回應，與事件 3 同時段發生，後確認為合法 TXT 記錄。',
      outcome: '擱置',
      resolvedAt: '2025-09-12 17:30',
      resolvedBy: 'Frank Liu',
      resolution: '觀察後確認為誤報，列入持續觀察清單，搭配 PCAP 監控。',
    },
  ],
  6: [],
}

export function getMockReply(userMsg, issue, allIssues) {
  if (!issue) {
    const highP = allIssues.filter((x) => x.starRank >= 4 && x.currentStatus === '未處理')
    const criticals = allIssues.filter((x) => x.starRank === 5)
    return `【全局資安態勢摘要 — 2026-02-23】\n\n目前清單共 ${allIssues.length} 筆異常事件：\n‣ 最高危（5星）：${criticals.length} 筆 — 需立即處置\n‣ 高優先未處理（4星以上）：${highP.length} 筆\n\n【建議優先處置順序】\n1. Issue #1（5★）DNS C2 Tunneling — 立即隔離 192.168.10.20\n2. Issue #4（4★）暴力破解 — 立即查看是否已有成功登入\n3. Issue #2（4★）SVR_to_WAN 策略 — 今日內收緊防火牆規則\n4. Issue #3（4★）VPN DNS 注入 — 今日完成 PCAP 鑑識\n\n你有特別想討論哪個事件嗎？`
  }
  const kb = mockKnowledge[issue.id]
  if (!kb) return `關於「${issue.title}」，目前無詳細分析資料，請查看事件詳情頁的建議處置方法。`
  const msg = userMsg.toLowerCase()
  if (
    msg.includes('摘要') ||
    msg.includes('整體') ||
    msg.includes('summary') ||
    msg.includes('overview')
  )
    return kb.摘要
  if (
    msg.includes('ioc') ||
    msg.includes('發現') ||
    msg.includes('指標') ||
    msg.includes('indicator') ||
    msg.includes('來源')
  )
    return kb.發現
  if (
    msg.includes('說明') ||
    msg.includes('原理') ||
    msg.includes('技術') ||
    msg.includes('背景') ||
    msg.includes('什麼是') ||
    msg.includes('補充')
  )
    return kb.說明
  if (
    msg.includes('修復') ||
    msg.includes('處置') ||
    msg.includes('修補') ||
    msg.includes('fix') ||
    msg.includes('remediat') ||
    msg.includes('建議')
  )
    return kb.修復
  if (
    msg.includes('步驟') ||
    msg.includes('指令') ||
    msg.includes('command') ||
    msg.includes('cli') ||
    msg.includes('執行') ||
    msg.includes('操作')
  ) {
    const stepKeys = Object.keys(kb.步驟前綴)
    for (const k of stepKeys) {
      if (kb.步驟前綴[k]) return kb.步驟前綴[k]
    }
  }
  return (
    kb.摘要 +
    '\n\n您可以繼續詢問：整體摘要、相關 IOC 發現、技術背景說明、修復建議、或具體操作步驟。'
  )
}

export function getStepReply(issue, stepIdx) {
  const kb = mockKnowledge[issue.id]
  if (kb && kb.步驟前綴[stepIdx]) return kb.步驟前綴[stepIdx]
  const step = issue.suggests[stepIdx] || ''
  return (
    `【參考步驟 ${stepIdx + 1} — 詳細說明】\n\n` +
    step +
    `\n\n【通用執行程序】\n\n1. 在進行任何操作前，先記錄目前系統狀態（截圖/日誌備份）\n2. 在測試環境驗證指令後，再套用至生產環境\n3. 每個步驟完成後，記錄於處置紀錄（時間、操作人員、結果）\n4. 若操作影響業務服務，需先取得主管授權並通知相關部門\n\n如需更具體的操作指令，請告訴我您使用的設備型號與版本。`
  )
}
