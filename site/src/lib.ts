import servicesData from "./data/service-pages.json";
import doctorsData from "./data/doctors.json";
import pricesData from "./data/prices.json";
import reviewsData from "./data/reviews.json";
import promosData from "./data/promos.json";
import faqData from "./data/faq.json";
import contactsData from "./data/contacts.json";
import imgMap from "./data/img-map.json";
import widgets from "./data/widgets.json";

export const BASE_URL = "https://balashikha.neoplus-clinic.ru";

export const services = servicesData as ServicePage[];
export const doctors = doctorsData as Doctor[];
export const priceGroups = (pricesData as PriceData).groups;
export const reviews = (reviewsData as ReviewsData).items;
export const promos = (promosData as PromosData).items;
export const faqGroups = (faqData as FaqData).groups;
export const contacts = contactsData as Contacts;
export const widgets_ = widgets;

export interface ServicePage {
  url: string;
  path: string;
  title: string;
  description: string;
  h1: string;
  canonical_override?: string | null;
  prices: PriceRow[];
  price_header?: string[] | null;
  faq: { q: string; a: string }[];
  sections: Section[];
  hero_facts?: string[];
  consultation_links?: { href: string; label: string }[];
  hero_lead?: string;
  hero_price?: string;
  hero_sub?: string;
  hero_img?: string;
  direction?: string;
}
export interface PriceRow { name: string; price: string | null; desc?: string; term?: string }
export interface Section { section: string; heading: string | null; items: { tag: string; text: string }[] }
export interface Doctor {
  name: string; specialty: string; url: string; photo: string;
  profile?: {
    h1?: string; education: string[]; experience: string[]; schedule: string[];
    specialization: string[]; documents: string[]; photo_page?: string;
    diploma_images: string[];
  };
}
export interface PriceData { groups: { group: string; items: PriceRow[] }[] }
export interface ReviewsData { count: number; items: Review[] }
export interface Review { author: string; age: string; text: string; avatar: string; source_icon: string; date: string }
export interface PromosData { count: number; items: Promo[] }
export interface Promo { title: string; text: string; image: string }
export interface FaqData { groups: { group: string; items: { q: string; a: string }[] }[] }
export interface Contacts {
  phones: string[]; emails: string[];
  address_contact_center: string;
  legal_entity: string; inn: string; ogrn: string;
  license_main: { number: string; date: string; address: string };
  license_stacionar_partner: { entity: string; number: string; date: string; address: string };
}

export const PHONE_MAIN = "+7 (800) 200-24-46";
export const PHONE_MAIN_TEL = "+78002002446";
export const PHONE_MOBILE = "+7 960 442-04-15";
export const PHONE_MOBILE_TEL = "+79604420415";
export const EMAIL_MAIN = "balashikha@neoplus-clinic.ru";

/** Map an old-site image URL to the local optimized copy (or undefined). */
export function img(oldUrl: string | undefined | null): string | undefined {
  if (!oldUrl) return undefined;
  const full = oldUrl.startsWith("http") ? oldUrl : BASE_URL + oldUrl;
  const clean = full.split("?")[0];
  return (imgMap as Record<string, string>)[clean];
}

export function telHref(phone: string): string {
  return "tel:" + phone.replace(/[^+\d]/g, "");
}

/** "Вывод из запоя: Экспресс-капельница" — strip clinic suffix from long H1s for cards */
export function shortServiceName(h1: string): string {
  return h1
    .replace(/\s*(в|во)\s*(наркологическ|клиник|медиц)[^,]*/gi, "")
    .replace(/\s*Балашихинский наркологический центр\s*/gi, " ")
    .replace(/\s{2,}/g, " ")
    .replace(/\s+и на дому\s*$/i, "")
    .trim() || h1;
}

const DIRECTION_ORDER = [
  "Алкоголизм",
  "Наркомания",
  "Кодирование",
  "Психиатрия",
  "Реабилитация",
  "Консультации",
];

export function directions(): { name: string; services: ServicePage[] }[] {
  const map = new Map<string, ServicePage[]>();
  for (const s of services) {
    const d = s.direction || "Другое";
    if (!map.has(d)) map.set(d, []);
    map.get(d)!.push(s);
  }
  const out = DIRECTION_ORDER.filter((d) => map.has(d)).map((d) => ({
    name: d,
    services: map.get(d)!,
  }));
  const rest = [...map.keys()].filter((k) => !DIRECTION_ORDER.includes(k));
  for (const k of rest) out.push({ name: k, services: map.get(k)! });
  return out;
}

/** Цена «от X ₽» для плитки каталога: первая числовая цена из прайса услуги. */
export function servicePriceText(s: ServicePage): string | null {
  const row =
    s.prices.find((r) => r.price && /\d/.test(r.price)) ??
    s.prices.find((r) => /бесплатно/i.test(r.price ?? ""));
  if (!row?.price) return null;
  return row.price.replace(/(\d)\s*₽/, "$1 ₽").trim();
}

