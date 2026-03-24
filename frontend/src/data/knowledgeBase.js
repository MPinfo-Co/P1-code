export const knowledgeBases = [
  {
    id: 1,
    name: '資安相關',
    desc: '資安事件應變 SOP、防火牆政策、安全規範等資安相關文件與資料。',
    boundPartners: ['security-expert'],
    accessRoles: ['管理員', '一般使用者'],
    docs: [
      { id: 'd01', name: '資安事件應變SOP_v3.pdf', size: '245 KB', uploadDate: '2026-01-15' },
      { id: 'd02', name: '防火牆政策白名單_IT.txt', size: '12 KB', uploadDate: '2026-01-20' },
      { id: 'd03', name: '資安通報流程_2026Q1.pdf', size: '180 KB', uploadDate: '2026-02-01' },
      { id: 'd04', name: 'Fortinet_Best_Practice_Guide.pdf', size: '1.2 MB', uploadDate: '2026-01-08' },
      { id: 'd05', name: 'Windows_Security_Event_ID_Reference.pdf', size: '890 KB', uploadDate: '2026-01-10' },
    ],
    tables: [
      {
        id: 't1',
        name: '設備資產表',
        createdDate: '2026-01-10',
        columns: ['設備名稱', 'IP 位址', 'MAC 位址', '作業系統', '負責人', '位置', '備註'],
        rows: [
          ['MPIDCFW', '192.168.1.1', '00:09:0F:AA:BB:01', 'FortiOS 7.4', 'Rex Shen', 'IDC 機房 A', '主防火牆'],
          ['DC-SVR-01', '192.168.10.20', '00:50:56:B2:11:22', 'Windows Server 2022', 'Dama Wang', 'IDC 機房 B', '主 DNS 伺服器'],
        ],
      },
      {
        id: 't2',
        name: '安全 IP 白名單',
        createdDate: '2026-02-01',
        columns: ['IP / CIDR', '說明', '加入日期', '負責人'],
        rows: [
          ['192.168.1.100', 'IT 掃描主機', '2026-01-05', 'Rex Shen'],
          ['10.0.0.0/8', '內部 VPN 網段', '2026-01-05', 'Rex Shen'],
        ],
      },
    ],
  },
]
