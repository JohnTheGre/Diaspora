import { writable } from 'svelte/store';

export const activeFilterType = writable(null); // 'height' | 'weight' | 'language' | 'diaspora' | null
export const heightValue = writable(150);
export const weightValue = writable(70);
export const selectedLanguages = writable(new Set());
export const selectedDiasporas = writable(new Set());
export const comparisonOpen = writable(false);