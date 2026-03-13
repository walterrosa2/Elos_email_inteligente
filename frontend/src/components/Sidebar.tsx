import { LayoutDashboard, FileText, Settings, LogOut, Users, Clock, FileSpreadsheet } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

export function Sidebar() {
  const { user, logout } = useAuthStore();
  const isAdmin = user?.role === 'admin';

  return (
    <div className="flex flex-col w-64 h-screen px-4 py-8 bg-white border-r">
      <h2 className="text-3xl font-semibold text-gray-800 text-center mb-8">ELOS <span className="text-blue-600">Sync</span></h2>
      <div className="flex flex-col justify-between flex-1 mt-6">
        <nav>
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `flex items-center px-4 py-2 text-gray-700 bg-gray-100 rounded-lg ${isActive ? 'bg-blue-50 text-blue-700 font-bold' : 'hover:bg-gray-200'}`
            }
          >
            <LayoutDashboard size={20} className="mr-3" />
            <span className="mx-2 font-medium">Dashboard</span>
          </NavLink>

          <NavLink
            to="/analysis"
            className={({ isActive }) =>
              `flex items-center px-4 py-2 mt-5 text-gray-700 rounded-lg ${isActive ? 'bg-blue-50 text-blue-700 font-bold' : 'hover:bg-gray-200'}`
            }
          >
            <FileText size={20} className="mr-3" />
            <span className="mx-2 font-medium">Análise e Extração</span>
          </NavLink>

          <NavLink
            to="/reports"
            className={({ isActive }) =>
              `flex items-center px-4 py-2 mt-5 text-gray-700 rounded-lg ${isActive ? 'bg-blue-50 text-blue-700 font-bold' : 'hover:bg-gray-200'}`
            }
          >
            <FileSpreadsheet size={20} className="mr-3" />
            <span className="mx-2 font-medium">Relatórios</span>
          </NavLink>

          <NavLink
            to="/schedule"
            className={({ isActive }) =>
              `flex items-center px-4 py-2 mt-5 text-gray-700 rounded-lg ${isActive ? 'bg-blue-50 text-blue-700 font-bold' : 'hover:bg-gray-200'}`
            }
          >
            <Clock size={20} className="mr-3" />
            <span className="mx-2 font-medium">Agendamento</span>
          </NavLink>

          {isAdmin && (
            <>
              <div className="mt-8 mb-4">
                <span className="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Admin
                </span>
              </div>
              <NavLink
                to="/contracts"
                className={({ isActive }) =>
                  `flex items-center px-4 py-2 text-gray-700 rounded-lg ${isActive ? 'bg-blue-50 text-blue-700 font-bold' : 'hover:bg-gray-200'}`
                }
              >
                <Users size={20} className="mr-3" />
                <span className="mx-2 font-medium">Gestão de Contratos</span>
              </NavLink>

              <NavLink
                to="/settings"
                className={({ isActive }) =>
                  `flex items-center px-4 py-2 mt-5 text-gray-700 rounded-lg ${isActive ? 'bg-blue-50 text-blue-700 font-bold' : 'hover:bg-gray-200'}`
                }
              >
                <Settings size={20} className="mr-3" />
                <span className="mx-2 font-medium">Configurações Base</span>
              </NavLink>
            </>
          )}
        </nav>

        <div className="flex items-center px-4 -mx-2 mb-4 cursor-pointer hover:bg-red-50 p-2 rounded-lg text-red-600" onClick={logout}>
          <LogOut size={20} className="mr-3" />
          <span className="font-semibold">Sair da Conta</span>
        </div>
      </div>
    </div>
  );
}
