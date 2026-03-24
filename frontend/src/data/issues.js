export const suggestRefs = {
  1: [
    [{ type: 'mitre', label: 'T1071.004', name: 'DNS Tunneling', url: 'https://attack.mitre.org/techniques/T1071/004/' }],
    [{ type: 'mitre', label: 'T1568.002', name: 'DGA', url: 'https://attack.mitre.org/techniques/T1568/002/' }, { type: 'ref', label: 'VirusTotal: 180.76.76.95', url: 'https://www.virustotal.com/gui/ip-address/180.76.76.95' }],
    [{ type: 'mitre', label: 'T1573.001', name: 'Encrypted Channel', url: 'https://attack.mitre.org/techniques/T1573/001/' }],
  ],
  2: [
    [{ type: 'ref', label: 'NIST SP 800-41', url: 'https://csrc.nist.gov/publications/detail/sp/800-41/rev-1/final' }, { type: 'mitre', label: 'T1190', name: 'Exploit Public-Facing App', url: 'https://attack.mitre.org/techniques/T1190/' }],
    [{ type: 'ref', label: 'Fortinet GeoIP Config', url: 'https://docs.fortinet.com/document/fortigate/' }],
  ],
  3: [
    [{ type: 'mitre', label: 'T1105', name: 'Ingress Tool Transfer', url: 'https://attack.mitre.org/techniques/T1105/' }, { type: 'ref', label: 'dnscat2', url: 'https://github.com/iagox86/dnscat2' }],
    [],
    [],
  ],
  4: [
    [{ type: 'mitre', label: 'T1110.001', name: 'Password Guessing', url: 'https://attack.mitre.org/techniques/T1110/001/' }],
    [{ type: 'ref', label: 'Fortinet IPS Sensor', url: 'https://docs.fortinet.com/document/fortigate/' }],
    [],
  ],
  5: [
    [],
    [{ type: 'ref', label: 'RFC 6891: EDNS(0)', url: 'https://tools.ietf.org/html/rfc6891' }],
    [{ type: 'mitre', label: 'T1071.004', name: 'DNS C2', url: 'https://attack.mitre.org/techniques/T1071/004/' }],
  ],
  6: [
    [{ type: 'mitre', label: 'T1595', name: 'Active Scanning', url: 'https://attack.mitre.org/techniques/T1595/' }],
    [],
  ],
}

export const suggestUrgency = {
  1: ['最推薦', '次推薦', '可選'],
  2: ['最推薦', '次推薦'],
  3: ['最推薦', '次推薦', '可選'],
  4: ['最推薦', '次推薦', '可選'],
  5: ['最推薦', '次推薦', '可選'],
  6: ['最推薦', '次推薦'],
}

export const issues = [
  {
    id: 1,
    partnerId: 'security-expert',
    title: '核心攻擊：內部 DNS 伺服器 192.168.10.20 淪陷與進階 DNS C2 通訊',
    starRank: 5,
    date: '2026-02-21',
    dateEnd: '2026-02-23',
    affectedSummary: '1 台伺服器（DNS）',
    affected: '192.168.10.20（內部主要 DNS 伺服器）→ 180.76.76.95（Baidu DNS）等 258 個外部 IP',
    currentStatus: '未處理',
    history: [],
    desc: `【異常發現】偵測到該伺服器向 180.76.76.95 (Baidu DNS) 等高風險 IP 發出異常頻率的 DNS 查詢（595 筆/10h），且目的地分散於 258 個不同外部 IP。\n【風險分析】行為具備 Fast-flux 特徵，其傳輸字元長度（sentbyte 89-112 B）顯示其非正常解析請求，而是進行高度加密的 C2 Beaconing（心跳包）。\n此為 APT 等級攻擊，利用 DNS 協定作為隧道（Tunneling）來繞過傳統防火牆的檢查。攻擊者將 DNS 伺服器作為 C2 通訊橋樑，透過加密 DNS 查詢持續維持對受害網路的控制能力。`,
    suggests: [
      '立即於 Fortigate 移除 192.168.10.20 的任意出站權限。Fortinet Code: config firewall policy -> edit <id> -> set dstaddr "all" (change to specific list) -> set service "DNS" -> set action deny。MITRE: T1071.004 (DNS Tunneling)。',
      '在 Windows Server 端清查轉發設定，確認是否存在惡意轉發器。PowerShell: Get-DnsServerForwarder，檢查是否包含 180.76.76.95。MITRE: T1568.002 (Domain Generation Algorithms)。',
      '針對該主機啟動 IR 鑑識流程，搜尋惡意 DLL 組件。MITRE: T1573.001 (Encrypted Channel)。',
    ],
    logs: [
      'date=2026-02-23 time=13:45:10 devname="MPIDCFW" logid="0000000013" type="traffic" srcip=192.168.10.20 dstip=180.76.76.95 dstport=53 dstcountry="China" action="accept" policyid=1 policyname="SVR_to_WAN" service="DNS" sentbyte=78 rcvdbyte=156 [★ KEY IOC：百度公共DNS]',
      'date=2026-02-23 time=09:13:37 devname="MPIDCFW" logid="0000000013" type="traffic" srcip=192.168.10.20 dstip=204.14.183.224 dstport=53 dstcountry="United States" action="accept" policyid=1 policyname="SVR_to_WAN" service="DNS" sentbyte=104 rcvdbyte=120',
      '（外部 DNS 共 595 筆，目的地 258 個 IP；國家分布：美國 515 / 台灣 29 / 荷蘭 26 / 中國 7 / 新加坡 6）',
    ],
    mitre: [
      { id: 'T1071.004', name: 'Application Layer Protocol: DNS', url: 'https://attack.mitre.org/techniques/T1071/004/' },
      { id: 'T1568.002', name: 'Dynamic Resolution: DGA', url: 'https://attack.mitre.org/techniques/T1568/002/' },
      { id: 'T1573.001', name: 'Encrypted Channel', url: 'https://attack.mitre.org/techniques/T1573/001/' },
    ],
    refs: [
      { name: 'VirusTotal: 180.76.76.95', url: 'https://www.virustotal.com/gui/ip-address/180.76.76.95' },
      { name: 'MITRE APT41 Group', url: 'https://attack.mitre.org/groups/G0096/' },
    ],
  },
  {
    id: 2,
    partnerId: 'security-expert',
    title: '基礎架構風險：SVR_to_WAN 策略配置過於寬鬆',
    starRank: 4,
    date: '2026-02-22',
    dateEnd: '2026-02-23',
    affectedSummary: '伺服器段 192.168.10.0/24（全球 11 國）',
    affected: 'mpidcfw / policyid=1 (SVR_to_WAN) → 任意外部 IP，無地理限制',
    currentStatus: '未處理',
    history: [],
    desc: `【異常發現】防火牆策略 policyid=1 (SVR_to_WAN) 允許伺服器段直接建立與外部 IP 的任何連線，且無地理限制。\n這是導致事件 1 能夠成功建立 C2 通道的「根源性弱點」。若無此寬鬆權限，惡意程式無法將資料回傳至中國或荷蘭境內的伺服器。此策略問題屬基礎架構安全缺陷，應優先修復，否則即使清除本次惡意軟體，攻擊者仍可透過相同路徑重新滲透。`,
    suggests: [
      '建立目的地 FQDN 白名單，僅允許必要的業務更新（如 Microsoft Update）。Fortinet Code: set dstaddr-negate enable（排除白名單後其餘全封）。MITRE: T1190 (Exploit Public-Facing Application)。',
      '啟用 GeoIP 過濾功能，拒絕所有來自非業務往來國家（如 CN, RU）的連線。Fortinet Code: config firewall address -> edit "Block_List" -> set type geoip -> set country "CN" "RU"。',
    ],
    logs: [
      'date=2026-02-23 time=09:47:23 srcip=192.168.10.20 dstip=180.76.76.95 dstcountry="China" service="DNS" action="accept" policyid=1 policyname="SVR_to_WAN" [根因：C2 查詢至百度DNS 得以成立]',
      'date=2026-02-23 time=09:13:37 srcip=192.168.10.20 dstip=204.14.183.224 dstcountry="United States" service="DNS" action="accept" policyid=1 policyname="SVR_to_WAN" [根因：DNS Tunneling 外部查詢得以成立]',
    ],
    mitre: [
      { id: 'T1190', name: 'Exploit Public-Facing Application', url: 'https://attack.mitre.org/techniques/T1190/' },
    ],
    refs: [
      { name: 'NIST SP 800-41 Firewall Guidelines', url: 'https://csrc.nist.gov/publications/detail/sp/800-41/rev-1/final' },
      { name: 'Fortinet Best Practice Guide', url: 'https://docs.fortinet.com/document/fortigate/' },
    ],
  },
  {
    id: 3,
    partnerId: 'security-expert',
    title: '橫向移動威脅：VPN 用戶端 172.18.1.62 遭受超大 DNS Payload 注入',
    starRank: 3,
    date: '2026-02-23',
    dateEnd: '2026-02-23',
    affectedSummary: '1 台 VPN 用戶端',
    affected: 'mpidcfw / 172.18.1.62（VPN 用戶端）← 192.168.10.20（疑似遭入侵 DNS）',
    currentStatus: '未處理',
    history: [],
    desc: `【異常發現】VPN 用戶端從內部 DNS (192.168.10.20) 收到 rcvdbyte=2.29 KB 的超大型回應，遠超 DNS 標準上限 512 bytes。\n【風險分析】行為模式符合 dnscat2 或 iodine 的指令傳輸特徵，顯示攻擊者正從已淪陷的伺服器對內部終端進行 Payload 注入。若 192.168.10.20 已遭入侵，此 2.29 KB 超大回應可能為 DNS Tunneling 工具向 VPN 用戶端發送的加密指令，構成惡意軟體橫向傳播路徑。`,
    suggests: [
      '側錄該用戶端 DNS 解析內容，尋找高熵值（Entropy）的子域名加密字串。MITRE: T1105 (Ingress Tool Transfer)。',
      '在該設備端強制執行 DNS 快取清理。Command: ipconfig /flushdns。',
      '確認 172.18.1.62 設備身份與對應使用者，評估設備健康狀態，執行端點掃描確認是否存在 dnscat2 或 iodine 等 DNS 工具。',
    ],
    logs: [
      'date=2026-02-23 time=13:29:51 srcip=172.18.1.62 srcintf="To_TP_Fortigate" dstip=192.168.10.2 dstport=53 action="accept" policyid=52 vpntype="ipsecvpn" sentbyte=809 rcvdbyte=2341 [★ 異常：2.29 KB 超 DNS 標準]',
      'date=2026-02-23 time=13:45:10 srcip=172.18.1.62 dstip=192.168.10.2 dstport=53 action="accept" policyid=52 vpntype="ipsecvpn" sentbyte=623 rcvdbyte=2202 [★ 異常：2.15 KB]',
    ],
    mitre: [
      { id: 'T1105', name: 'Ingress Tool Transfer', url: 'https://attack.mitre.org/techniques/T1105/' },
      { id: 'T1071.004', name: 'Application Layer Protocol: DNS', url: 'https://attack.mitre.org/techniques/T1071/004/' },
    ],
    refs: [
      { name: 'dnscat2 GitHub', url: 'https://github.com/iagox86/dnscat2' },
      { name: 'iodine DNS Tunnel', url: 'https://github.com/yarrick/iodine' },
    ],
  },
  {
    id: 4,
    partnerId: 'security-expert',
    title: '外部攻擊監測：針對行政帳號的分散式暴力破解 (Brute Force)',
    starRank: 2,
    date: '2026-02-20',
    dateEnd: '2026-02-23',
    affectedSummary: 'Administrator / mp0391 帳號',
    affected: 'Windows Server / Administrator、mp0391 帳號 ← Netherlands 等地外部來源',
    currentStatus: '未處理',
    history: [],
    desc: `【異常發現】全日監測到針對 Administrator 與 mp0391 帳號的數百次失敗登入嘗試，來源包含 Netherlands 等地。\n攻擊者採行「低速慢攻（Low and Slow）」策略，試圖規避常見的帳號鎖定偵測。結合事件 2（SVR_to_WAN 寬鬆策略），若暴力破解成功，攻擊者將直接獲得伺服器段高權限存取能力，危害極大。`,
    suggests: [
      '針對所有具備管理員權限的帳號強制啟用多因素驗證。MITRE: T1110.001 (Password Guessing)。',
      '結合 Fortigate 的 IPS 特徵庫，自動封鎖頻繁嘗試失敗的來源 IP。Fortinet Code: config ips sensor -> edit "default" -> config entries -> set action block。',
      '稽核 Administrator 與 mp0391 帳號近 30 天的登入紀錄，確認是否有異常成功登入事件。',
    ],
    logs: [
      'Windows Security EventID=4625 （登入失敗）TargetUserName=Administrator LogonType=3 IpAddress=荷蘭 [Part 13 集中發生]',
      'Windows Security EventID=4625 TargetUserName=mp0391 LogonType=3 IpAddress=保加利亞 [Part 28 集中發生]',
      '（多筆失敗登入，目前均被防火牆攔截，尚無成功登入紀錄）',
    ],
    mitre: [
      { id: 'T1110.001', name: 'Brute Force: Password Guessing', url: 'https://attack.mitre.org/techniques/T1110/001/' },
    ],
    refs: [
      { name: 'NIST MFA Guidelines', url: 'https://pages.nist.gov/800-63-3/' },
    ],
  },
  {
    id: 5,
    partnerId: 'security-expert',
    title: '低危險追蹤：VPN 用戶端 172.18.1.61 異常封包 (1.24 KB)',
    starRank: 2,
    date: '2026-02-23',
    dateEnd: '2026-02-23',
    affectedSummary: '1 台 VPN 用戶端',
    affected: 'mpidcfw / 172.18.1.61（VPN 用戶端）← 192.168.10.2 / 192.168.10.20',
    currentStatus: '未處理',
    history: [],
    desc: `【異常發現】偵測到超出標準但規模較小的 DNS 回應（rcvdbyte=1.24 KB）。雖然目前可能為合法的資源紀錄（如 TXT），但因與事件 3 同時段發生，需預防其為攻擊的前導探測。\n與事件 3（172.18.1.62，2.29 KB）同時段、同目的 DNS 伺服器，兩個 VPN 用戶端均收到大型 DNS 回應，可能代表 DNS C2 工具的廣播式指令分發行為。在確認 192.168.10.20 狀態前，列為追蹤觀察。`,
    suggests: [
      '於監控系統建立流量閾值，針對 > 2KB 封包才觸發高優先級告警，優化 SOC 分析效能。',
      '結合事件 3（172.18.1.62）一起進行 PCAP 分析，比對兩台設備的大型 DNS 回應是否含相同 payload 特徵。',
      '在事件 1（192.168.10.20 入侵確認/排除）後重新評估本事件風險等級。MITRE: T1071.004 (DNS Tunneling)。',
    ],
    logs: [
      'date=2026-02-23 time=13:45:12 srcip=172.18.1.61 dstip=192.168.10.2 dstport=53 action="accept" policyid=52 vpntype="ipsecvpn" sentbyte=459 rcvdbyte=1270 [★ 異常：1.24 KB]',
      'date=2026-02-23 time=11:48:46 srcip=172.18.1.61 dstip=192.168.10.2 dstport=53 action="accept" policyid=52 vpntype="ipsecvpn" sentbyte=252 rcvdbyte=556',
    ],
    mitre: [
      { id: 'T1071.004', name: 'Application Layer Protocol: DNS', url: 'https://attack.mitre.org/techniques/T1071/004/' },
    ],
    refs: [
      { name: 'RFC 6891: EDNS(0) Extension', url: 'https://tools.ietf.org/html/rfc6891' },
    ],
  },
  {
    id: 6,
    partnerId: 'security-expert',
    title: '環境雜訊：外部高風險地理來源連線攔截（正常防禦，173 萬筆）',
    starRank: 1,
    date: '2026-02-23',
    dateEnd: '2026-02-23',
    affectedSummary: '全域防火牆（173 萬筆已攔截）',
    affected: 'mpidcfw / WAN 介面 ← Netherlands、France 等高危地區自動化掃描',
    currentStatus: '處理中',
    history: [
      { date: '2026-02-23 10:15', user: 'Rex Shen', note: '已確認為正常背景雜訊，列入週報觀察。', statusChange: '處理中' },
    ],
    desc: `【異常發現】全日高達 173 萬筆防火牆日誌多為外部自動化掃描。雖然來自 Netherlands、France 等高危地區，但均已被 action="deny" 成功攔截。\n此類事件為網際網路常態性背景雜訊，代表防火牆邊界防禦正常運作。此類事件不應納入即時告警，建議整合為週報供管理層參閱，以降低 SOC 分析師工作量。`,
    suggests: [
      '建議將此類雜訊整合為週報，不納入即時告警，減少分析師工作量。MITRE: T1595 (Active Scanning)。',
      '持續監控攔截日誌，若發現特定來源 IP 在短時間內重複掃描，可考慮加入動態封鎖清單。',
    ],
    logs: [
      'date=2026-02-23 time=xx:xx:xx dstip=211.21.43.178 srcip=Netherlands action="deny" policyid=0 [正常攔截]',
      'date=2026-02-23 time=xx:xx:xx dstip=211.21.43.178 srcip=France action="deny" policyid=0 [正常攔截]',
      '（全日共 1,735,168 筆防火牆日誌，多數為 action=deny 的外部掃描，屬環境雜訊）',
    ],
    mitre: [
      { id: 'T1595', name: 'Active Scanning', url: 'https://attack.mitre.org/techniques/T1595/' },
    ],
    refs: [],
  },
]
