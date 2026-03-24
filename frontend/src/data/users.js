export const users = [
  { id: 1, name: 'Rex Shen',     email: 'rexshen@mpinfo.com.tw',     roles: ['管理員'] },
  { id: 2, name: 'Robert Huang', email: 'roberthuang@mpinfo.com.tw',  roles: ['一般使用者'] },
  { id: 3, name: 'Pong Chang',   email: 'pongchang@mpinfo.com.tw',    roles: ['一般使用者'] },
  { id: 4, name: 'Dama Wang',    email: 'damawang@mpinfo.com.tw',     roles: ['管理員'] },
  { id: 5, name: 'Frank Liu',    email: 'frankliu@mpinfo.com.tw',     roles: ['管理員'] },
]

export const roles = [
  {
    id: 1,
    name: '管理員',
    partners: ['資安專家'],
    canAccessAI: true,
    canManageAccounts: true,
    canManageRoles: true,
    canEditAI: true,
  },
  {
    id: 2,
    name: '一般使用者',
    partners: ['資安專家'],
    canAccessAI: true,
    canManageAccounts: false,
    canManageRoles: false,
    canEditAI: false,
  },
]
