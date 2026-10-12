"use server";

import { redirect } from "next/navigation";

import { authedJson } from "@/lib/auth";
import { type FormError, toFormError } from "@/lib/form-errors";

export type NewDocumentState = (FormError & { title?: string; text?: string }) | undefined;

export async function createTextDocument(
  _: NewDocumentState,
  formData: FormData,
): Promise<NewDocumentState> {
  const title = String(formData.get("title") ?? "").trim();
  const text = String(formData.get("text") ?? "");
  let id: string;
  try {
    ({ id } = await authedJson<{ id: string }>("/documents", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, text }),
    }));
  } catch (error) {
    // Hand back what was typed, so a rejected paste isn't lost.
    return { ...toFormError(error), title, text };
  }
  // Pasted text is analysed during the request, so its insights exist now.
  redirect(`/documents/${id}`);
}

export async function uploadDocument(
  _: NewDocumentState,
  formData: FormData,
): Promise<NewDocumentState> {
  const file = formData.get("file");
  if (!(file instanceof File) || file.size === 0) {
    return { message: "Choose a .txt or .csv file to upload.", fieldErrors: {} };
  }
  const body = new FormData();
  body.append("file", file, file.name);
  let jobId: string;
  try {
    ({ job_id: jobId } = await authedJson<{ job_id: string }>("/documents/upload", {
      method: "POST",
      body,
    }));
  } catch (error) {
    // The API's own 413/415 messages say exactly what was wrong with the file.
    return toFormError(error);
  }
  // Uploads are analysed in the background: go and watch the job.
  redirect(`/jobs/${jobId}`);
}
