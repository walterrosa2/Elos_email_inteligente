import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';

export function DashboardLayout() {
  return (
    <div className="flex bg-gray-100 min-h-screen">
      <Sidebar />
      <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100">
        <Outlet />
      </main>
    </div>
  );
}
