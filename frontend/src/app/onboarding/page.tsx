import type { Metadata } from "next";
import { OnboardingClient } from "./onboarding-client";

export const metadata: Metadata = {
  title: "Complete Your Profile - Job Hunter",
  description:
    "Set up your Job Hunter profile to get matched with your ideal opportunities.",
};

export default function OnboardingPage() {
  return <OnboardingClient />;
}
