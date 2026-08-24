import { useEffect, useState } from "react";
import { toast } from "sonner";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { api, formatApiErrorDetail } from "@/lib/api";
import { Users, Briefcase, CircleDollarSign, MessageSquare, Activity } from "lucide-react";

const TABS = ["Bookings", "Clients", "Contacts"];

const statusColor = {
  new: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  quoted: "bg-purple-500/10 text-purple-400 border-purple-500/30",
  in_progress: "bg-[#FF7A00]/10 text-[#FF7A00] border-[#FF7A00]/40",
  completed: "bg-green-500/10 text-green-400 border-green-500/30",
  cancelled: "bg-red-500/10 text-red-400 border-red-500/30",
};

export default function AdminDashboard() {
  const [tab, setTab] = useState("Bookings");
  const [stats, setStats] = useState(null);
  const [bookings, setBookings] = useState([]);
  const [clients, setClients] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [editing, setEditing] = useState(null);
  const [edit, setEdit] = useState({ status: "", amount: "", admin_notes: "" });

  const load = async () => {
    try {
      const [s, b, c, ct] = await Promise.all([
        api.get("/admin/stats"),
        api.get("/admin/bookings"),
        api.get("/admin/clients"),
        api.get("/admin/contacts"),
      ]);
      setStats(s.data);
      setBookings(b.data);
      setClients(c.data);
      setContacts(ct.data);
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Failed to load admin data.");
    }
  };

  useEffect(() => { load(); }, []);

  const openEdit = (b) => {
    setEditing(b);
    setEdit({
      status: b.status,
      amount: b.amount ?? "",
      admin_notes: b.admin_notes ?? "",
    });
  };

  const saveEdit = async () => {
    try {
      await api.patch(`/admin/bookings/${editing.booking_id}`, {
        status: edit.status,
        amount: edit.amount === "" ? null : parseFloat(edit.amount),
        admin_notes: edit.admin_notes || null,
      });
      toast.success("Booking updated.");
      setEditing(null);
      await load();
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Save failed.");
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white" data-testid="admin-dashboard">
      <Navbar />
      <div className="max-w-7xl mx-auto px-6 py-14">
        <p className="overline mb-2">Admin Portal</p>
        <h1 className="font-heading text-4xl md:text-5xl font-extrabold tracking-tighter mb-10">Command Center</h1>

        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-10">
            <StatCard icon={Users} label="Clients" value={stats.total_clients} />
            <StatCard icon={Briefcase} label="Bookings" value={stats.total_bookings} />
            <StatCard icon={Activity} label="Active" value={stats.active_bookings} />
            <StatCard icon={MessageSquare} label="Contacts" value={stats.contact_messages} />
            <StatCard icon={CircleDollarSign} label="Revenue" value={`$${(stats.revenue || 0).toLocaleString()}`} />
          </div>
        )}

        <div className="flex gap-1 mb-6 border-b border-white/10">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              data-testid={`admin-tab-${t.toLowerCase()}`}
              className={`px-5 py-3 text-sm font-heading font-semibold border-b-2 transition-colors ${
                tab === t ? "border-[#FF7A00] text-[#FF7A00]" : "border-transparent text-white/60 hover:text-white"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        {tab === "Bookings" && (
          <div className="space-y-3" data-testid="admin-bookings-list">
            {bookings.length === 0 && <p className="text-white/60">No bookings yet.</p>}
            {bookings.map((b) => (
              <div key={b.booking_id} className="bg-[#141414] border border-white/10 p-5" data-testid={`admin-booking-${b.booking_id}`}>
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="overline mb-1">{b.service_title} · {b.booking_type}</p>
                    <h3 className="font-heading text-lg font-bold">{b.project_title}</h3>
                    <p className="text-sm text-white/60 mt-1">{b.client_name} · {b.client_email}</p>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <span className={`text-xs font-mono-accent px-3 py-1 border ${statusColor[b.status]}`}>{b.status.replace("_", " ")}</span>
                    <span className="text-xs text-white/60">Payment: {b.payment_status}</span>
                    {b.amount != null && <span className="text-[#FF7A00] font-bold">${b.amount.toLocaleString()}</span>}
                  </div>
                </div>
                <p className="text-white/70 text-sm mt-3">{b.requirements}</p>
                <div className="flex justify-end mt-3">
                  <button onClick={() => openEdit(b)} className="btn-outline text-xs py-2 px-4" data-testid={`admin-edit-btn-${b.booking_id}`}>
                    Update
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "Clients" && (
          <div className="bg-[#141414] border border-white/10 overflow-x-auto" data-testid="admin-clients-list">
            <table className="w-full text-sm">
              <thead className="bg-black/40 text-white/60 text-left">
                <tr>
                  <th className="p-4">Name</th>
                  <th className="p-4">Email</th>
                  <th className="p-4">Provider</th>
                  <th className="p-4">Joined</th>
                </tr>
              </thead>
              <tbody>
                {clients.map((c) => (
                  <tr key={c.user_id} className="border-t border-white/10">
                    <td className="p-4">{c.name}</td>
                    <td className="p-4 text-white/70">{c.email}</td>
                    <td className="p-4"><span className="font-mono-accent text-xs">{c.auth_provider}</span></td>
                    <td className="p-4 text-white/60">{new Date(c.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
                {clients.length === 0 && (
                  <tr><td colSpan="4" className="p-6 text-center text-white/50">No clients yet.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {tab === "Contacts" && (
          <div className="space-y-3" data-testid="admin-contacts-list">
            {contacts.length === 0 && <p className="text-white/60">No messages yet.</p>}
            {contacts.map((c) => (
              <div key={c.contact_id} className="bg-[#141414] border border-white/10 p-5">
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <h3 className="font-heading text-lg font-bold">{c.subject}</h3>
                    <p className="text-sm text-white/60">{c.name} · {c.email}</p>
                  </div>
                  <span className="text-xs text-white/40">{new Date(c.created_at).toLocaleString()}</span>
                </div>
                <p className="text-white/70 text-sm mt-3">{c.message}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {editing && (
        <div className="fixed inset-0 bg-black/80 grid place-items-center z-[100] p-4" onClick={() => setEditing(null)}>
          <div className="bg-[#141414] border border-white/10 p-8 max-w-lg w-full" onClick={(e) => e.stopPropagation()} data-testid="admin-edit-modal">
            <h3 className="font-heading text-2xl font-bold mb-4">Update Booking</h3>
            <div className="space-y-4">
              <div>
                <label className="overline">Status</label>
                <select
                  value={edit.status}
                  onChange={(e) => setEdit({ ...edit, status: e.target.value })}
                  className="mt-2 w-full bg-black/50 border border-white/15 focus:border-[#FF7A00] p-3"
                  data-testid="admin-edit-status"
                >
                  {["new", "quoted", "in_progress", "completed", "cancelled"].map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="overline">Quoted Amount (USD)</label>
                <input
                  type="number"
                  step="0.01"
                  value={edit.amount}
                  onChange={(e) => setEdit({ ...edit, amount: e.target.value })}
                  className="mt-2 w-full bg-black/50 border border-white/15 focus:border-[#FF7A00] p-3"
                  data-testid="admin-edit-amount"
                />
              </div>
              <div>
                <label className="overline">Admin Notes (visible to client)</label>
                <textarea
                  rows={4}
                  value={edit.admin_notes}
                  onChange={(e) => setEdit({ ...edit, admin_notes: e.target.value })}
                  className="mt-2 w-full bg-black/50 border border-white/15 focus:border-[#FF7A00] p-3 resize-none"
                  data-testid="admin-edit-notes"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={() => setEditing(null)} className="btn-outline flex-1 justify-center" data-testid="admin-edit-cancel">Cancel</button>
              <button onClick={saveEdit} className="btn-primary flex-1 justify-center" data-testid="admin-edit-save">Save</button>
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
}

function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="bg-[#141414] border border-white/10 p-5">
      <Icon className="w-5 h-5 text-[#FF7A00] mb-3" />
      <p className="font-heading text-2xl md:text-3xl font-extrabold">{value}</p>
      <p className="text-xs text-white/50 font-mono-accent mt-1">{label}</p>
    </div>
  );
}
