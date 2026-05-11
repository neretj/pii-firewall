import type { PipelineForm } from "@/lib/types";

// --- CONSTANTS ---
export const SESSION_KEY = "pf_auth";
export const CORRECT_HASH = "5510342bfc41b51576f8d2d88e052725d3a6a75e1192a8f2a1ad461abc4fc828";

// Language-specific test scenarios
export const DEMO_PROMPTS_BY_LANGUAGE: Record<string, string[]> = {
  es: [
    "Ana García tiene 43 años y su DNI es 12345678A. Tiene hipertensión.",
    "Ana G. vino hoy. Dice que su presión sanguínea sigue alta y pide seguimiento.",
    "También está su hermano Luis García con email luis.garcia@mail.com, 41 años.",
    "Compara Ana García con Ana García para validar continuidad de mapeo.",
    "Juan Pérez, nacido 15/03/1980, solicita revisión de sus análisis de colesterol.",
    "María López (IBAN ES9121000418450200051332) pregunta sobre opciones de financiación.",
    "Paciente José Martínez con teléfono +34612345678 reporta dolor en el pecho.",
    "Sofía Rodríguez, email sofia.r@example.com, necesita segunda opinión sobre cirugía.",
    "Carlos Fernández DNI 87654321B solicita copia de su historial médico completo.",
    "Isabel Gómez pregunta si puede compartir su caso con la Dra. Ana García.",
  ],
  en: [
    "John Smith is 55 years old and his SSN is 123-45-6789. He has diabetes.",
    "John S. came today. Says his blood sugar is still high and asks for follow-up.",
    "There's also his sister Sarah Smith with email sarah.s@example.com, 52 years old.",
    "Compare John Smith with John S. to validate mapping continuity.",
    "Emma Wilson, born 06/20/1985, requests review of her thyroid tests.",
    "Michael Brown (Account: 9876543210) asks about payment options.",
    "Patient David Lee with phone +1-555-0123 reports severe headaches.",
    "Lisa Anderson, email lisa.a@example.com, needs second opinion on treatment.",
    "Robert Martinez SSN 987-65-4321 requests copy of his complete medical records.",
    "Jennifer Garcia asks if she can share her case with Dr. Smith.",
  ],
  fr: [
    "Marie Dupont a 48 ans et son numéro INSEE est 2850312345678. Elle a du diabète.",
    "Marie D. est venue aujourd'hui. Dit que sa glycémie est toujours élevée et demande un suivi.",
    "Il y a aussi son frère Pierre Dupont avec email pierre.d@example.com, 45 ans.",
    "Comparer Marie Dupont avec Marie D. pour valider la continuité du mappage.",
    "Sophie Martin, née le 20/06/1985, demande la révision de ses tests thyroïdiens.",
    "Jean Bernard (IBAN FR7612345678901234567890123) demande des options de paiement.",
    "Patient Luc Rousseau avec téléphone +33612345678 rapporte des douleurs thoraciques.",
    "Claire Leroy, email claire.l@example.com, a besoin d'un deuxième avis sur le traitement.",
    "Thomas Blanc INSEE 1850312345678 demande une copie de son dossier médical complet.",
    "Isabelle Moreau demande si elle peut partager son cas avec Dr. Dupont.",
  ],
  de: [
    "Hans Müller ist 52 Jahre alt und seine Versicherungsnummer ist DE123456789. Er hat Diabetes.",
    "Hans M. kam heute. Sagt, sein Blutzucker ist immer noch hoch und bittet um Nachuntersuchung.",
    "Da ist auch seine Schwester Anna Müller mit E-Mail anna.mueller@example.com, 50 Jahre alt.",
    "Vergleichen Sie Hans Müller mit Hans M. um Mapping-Kontinuität zu validieren.",
    "Sophie Schmidt, geboren am 20.06.1985, bittet um Überprüfung ihrer Schilddrüsentests.",
    "Michael Weber (Konto: DE89370400440532013000) fragt nach Zahlungsoptionen.",
    "Patient Klaus Fischer mit Telefon +4915112345678 meldet starke Kopfschmerzen.",
    "Lisa Schneider, E-Mail lisa.s@example.com, braucht zweite Meinung zur Behandlung.",
    "Thomas Wagner Versicherung DE987654321 bittet um Kopie seiner vollständigen Krankenakte.",
    "Julia Koch fragt, ob sie ihren Fall mit Dr. Müller teilen kann.",
  ],
  it: [
    "Marco Rossi ha 50 anni e il suo codice fiscale è RSSMRC70A01H501X. Ha il diabete.",
    "Marco R. è venuto oggi. Dice che la sua glicemia è ancora alta e chiede un controllo.",
    "C'è anche sua sorella Anna Rossi con email anna.rossi@example.com, 48 anni.",
    "Confronta Marco Rossi con Marco R. per validare la continuità del mapping.",
    "Sofia Bianchi, nata il 20/06/1985, chiede revisione dei suoi test tiroidei.",
    "Luca Verdi (IBAN IT60X0542811101000000123456) chiede opzioni di pagamento.",
    "Paziente Giuseppe Russo con telefono +393123456789 riporta forti mal di testa.",
    "Elena Ferrari, email elena.f@example.com, ha bisogno di un secondo parere sul trattamento.",
    "Andrea Romano CF RMNAND80A01H501X chiede copia della sua cartella clinica completa.",
    "Chiara Colombo chiede se può condividere il suo caso con il Dr. Rossi.",
  ],
  pt: [
    "João Silva tem 48 anos e seu CPF é 123.456.789-00. Ele tem diabetes.",
    "João S. veio hoje. Diz que sua glicose ainda está alta e pede acompanhamento.",
    "Também está sua irmã Maria Silva com email maria.silva@example.com, 45 anos.",
    "Comparar João Silva com João S. para validar continuidade do mapeamento.",
    "Ana Santos, nascida em 20/06/1985, solicita revisão de seus exames de tireoide.",
    "Pedro Costa (Conta: 12345-6 78901-2) pergunta sobre opções de pagamento.",
    "Paciente Carlos Oliveira com telefone +5511987654321 relata fortes dores de cabeça.",
    "Mariana Ferreira, email mariana.f@example.com, precisa de segunda opinião sobre tratamento.",
    "Ricardo Souza CPF 987.654.321-00 solicita cópia de seu prontuário médico completo.",
    "Juliana Alves pergunta se pode compartilhar seu caso com o Dr. Silva.",
  ],
};

// Default prompts (Spanish for backward compatibility)
export const DEMO_PROMPTS = DEMO_PROMPTS_BY_LANGUAGE.es;

export const INITIAL_FORM: PipelineForm = {
  text: "",
  tenant_id: "tenant-demo",
  case_id: "case-demo",
  thread_id: "thread-1",
  actor_id: "user-demo",
  profile: "generic",
  detector_backend: "hybrid",
  language: "auto",
};

export type ApiPath = "/api/run" | "/api/forget";
