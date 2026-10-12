import { getDemoAccounts } from "@/lib/demo";

import { demoLogin } from "./actions";

const LABELS = { user: "Log in as the demo user", admin: "Log in as the admin" } as const;

export async function DemoButtons() {
  const accounts = await getDemoAccounts();
  if (accounts.length === 0) {
    return null;
  }
  return (
    <section aria-labelledby="demo" className="flex flex-col gap-3 border-t border-rule pt-6">
      <h2 id="demo" className="text-graphite">
        Just looking around? Use a demo account.
      </h2>
      {accounts.map((account) => (
        <form key={account.role} action={demoLogin.bind(null, account.role)}>
          <button type="submit" className="btn-outline">
            {LABELS[account.role]}
            <span className="text-sm font-normal text-graphite">{account.email}</span>
          </button>
        </form>
      ))}
    </section>
  );
}
