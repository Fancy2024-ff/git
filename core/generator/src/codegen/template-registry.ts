/**
 * 模板单一事实源（Generator Template Registry）。
 *
 * 正式模板 = 6 类 app_type 同名目录；base 为公共底座（非 app_type 主模板）。
 * ai-tool / ai-chat / ai-image 为 deprecated alias，统一归一化到正式模板。
 * 全项目 fallback 统一到 text_ai，不再 fallback 到 ai-tool。
 *
 * 与 core/capabilities/app_types.py 的 template 字段保持同名一致。
 */

/** 6 类正式模板（与 app_type 同名）。 */
export const OFFICIAL_TEMPLATES = [
  "text_ai",
  "image_ai",
  "ocr_scan",
  "speech_ai",
  "video_light",
  "utility_tool",
] as const;

export type OfficialTemplate = (typeof OFFICIAL_TEMPLATES)[number];

/** 公共底座目录（始终先复制，保证可构建）。非 app_type 主模板。 */
export const BASE_TEMPLATE = "base";

/** 默认 / fallback 模板。 */
export const DEFAULT_TEMPLATE: OfficialTemplate = "text_ai";

/** 废弃别名 → 正式模板。 */
export const DEPRECATED_ALIASES: Record<string, OfficialTemplate> = {
  "ai-tool": "text_ai",
  "ai-chat": "text_ai",
  "ai-image": "image_ai",
};

export function listOfficialTemplates(): OfficialTemplate[] {
  return [...OFFICIAL_TEMPLATES];
}

export function listDeprecatedAliases(): Record<string, OfficialTemplate> {
  return { ...DEPRECATED_ALIASES };
}

export function isOfficialTemplate(name: string): boolean {
  return (OFFICIAL_TEMPLATES as readonly string[]).includes(name);
}

/** 若是别名返回其正式名，否则原样返回。 */
export function resolveTemplateAlias(name: string): string {
  return DEPRECATED_ALIASES[name] ?? name;
}

/**
 * 归一化任意模板入参 → 正式模板名。
 * - base 保持 base（公共底座，调用方单独处理）
 * - 别名 → 正式名
 * - 正式名 → 原样
 * - 未知 → DEFAULT_TEMPLATE (text_ai)
 */
export function normalizeTemplateName(name: string | undefined | null): string {
  if (!name) return DEFAULT_TEMPLATE;
  if (name === BASE_TEMPLATE) return BASE_TEMPLATE;
  const resolved = resolveTemplateAlias(name);
  if (isOfficialTemplate(resolved)) return resolved;
  return DEFAULT_TEMPLATE;
}

/** 该名称（正式名或 base）是否为已知模板。别名先 resolve 再判断。 */
export function templateExists(name: string): boolean {
  if (name === BASE_TEMPLATE) return true;
  return isOfficialTemplate(resolveTemplateAlias(name));
}

export function getDefaultTemplate(): OfficialTemplate {
  return DEFAULT_TEMPLATE;
}

/** app_type → 正式模板名（同名约定；未知回退默认）。 */
export function getDefaultTemplateForAppType(appType: string | undefined | null): OfficialTemplate {
  if (appType && isOfficialTemplate(appType)) return appType as OfficialTemplate;
  return DEFAULT_TEMPLATE;
}
