// 事例を共有: 自分の成功事例を登録する。登録後は allCases / myCases に即時反映される。
import { PageHeader } from "@/components/PageHeader";
import { ShareForm } from "@/components/ShareForm";
import { useAppData } from "@/context/appDataContext";

export function SharePage() {
  const { clientId, handleCaseCreated } = useAppData();

  return (
    <>
      <PageHeader title="事例を共有" />
      <main className="mx-auto w-full max-w-2xl flex-1 px-6 py-8">
        <ShareForm clientId={clientId} onCreated={handleCaseCreated} />
      </main>
    </>
  );
}
