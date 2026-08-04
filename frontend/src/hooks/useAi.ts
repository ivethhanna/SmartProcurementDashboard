import { useMutation } from "@tanstack/react-query";
import { askAiChat, generateAiSummary } from "../services/api";

export function useAiChat() {
  return useMutation({
    mutationFn: askAiChat,
  });
}

export function useAiSummary() {
  return useMutation({
    mutationFn: generateAiSummary,
  });
}

