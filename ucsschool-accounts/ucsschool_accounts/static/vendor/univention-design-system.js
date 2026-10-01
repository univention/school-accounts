var Xe = Object.defineProperty;
var Ye = (i, e, t) => e in i ? Xe(i, e, { enumerable: !0, configurable: !0, writable: !0, value: t }) : i[e] = t;
var n = (i, e, t) => Ye(i, typeof e != "symbol" ? e + "" : e, t);
const qe = `@import"https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,400;0,600;1,400&display=swap";/*! tailwindcss v4.3.0 | MIT License | https://tailwindcss.com */@layer properties{@supports (((-webkit-hyphens:none)) and (not (margin-trim:inline))) or ((-moz-orient:inline) and (not (color:rgb(from red r g b)))){*,:before,:after,::backdrop{--tw-scale-x:1;--tw-scale-y:1;--tw-scale-z:1;--tw-rotate-x:initial;--tw-rotate-y:initial;--tw-rotate-z:initial;--tw-skew-x:initial;--tw-skew-y:initial;--tw-border-style:solid;--tw-leading:initial;--tw-font-weight:initial;--tw-tracking:initial;--tw-ordinal:initial;--tw-slashed-zero:initial;--tw-numeric-figure:initial;--tw-numeric-spacing:initial;--tw-numeric-fraction:initial;--tw-shadow:0 0 #0000;--tw-shadow-color:initial;--tw-shadow-alpha:100%;--tw-inset-shadow:0 0 #0000;--tw-inset-shadow-color:initial;--tw-inset-shadow-alpha:100%;--tw-ring-color:initial;--tw-ring-shadow:0 0 #0000;--tw-inset-ring-color:initial;--tw-inset-ring-shadow:0 0 #0000;--tw-ring-inset:initial;--tw-ring-offset-width:0px;--tw-ring-offset-color:#fff;--tw-ring-offset-shadow:0 0 #0000;--tw-outline-style:solid;--tw-blur:initial;--tw-brightness:initial;--tw-contrast:initial;--tw-grayscale:initial;--tw-hue-rotate:initial;--tw-invert:initial;--tw-opacity:initial;--tw-saturate:initial;--tw-sepia:initial;--tw-drop-shadow:initial;--tw-drop-shadow-color:initial;--tw-drop-shadow-alpha:100%;--tw-drop-shadow-size:initial}}}:root{--color-black:oklch(5% 0 0);--color-white:oklch(95% 0 0);--color-gray-800:oklch(15% 0 0);--color-gray-700:oklch(25% 0 0);--color-gray-600:oklch(35% 0 0);--color-gray-500:oklch(45% 0 0);--color-gray-400:oklch(55% 0 0);--color-gray-300:oklch(65% 0 0);--color-gray-200:oklch(75% 0 0);--color-gray-100:oklch(85% 0 0);--color-gray-50:oklch(90% 0 0);--color-red-200:oklch(94% .04 25);--color-red-300:oklch(83% .11 25);--color-red-400:oklch(72% .15 25);--color-red-500:oklch(57% .12 25);--color-red-600:oklch(52% .11 25);--color-red-700:oklch(42% .09 25);--color-red-800:oklch(32% .07 25);--color-red-900:oklch(24% .05 25);--color-coral-200:oklch(93% .04 70);--color-coral-300:oklch(82% .11 70);--color-coral-400:oklch(71% .15 70);--color-coral-500:oklch(56% .12 70);--color-coral-600:oklch(51% .11 70);--color-coral-700:oklch(41% .09 70);--color-coral-800:oklch(32% .07 70);--color-coral-900:oklch(24% .05 70);--color-pear-200:oklch(93% .04 115);--color-pear-300:oklch(81% .11 115);--color-pear-400:oklch(69% .15 115);--color-pear-500:oklch(55% .12 115);--color-pear-600:oklch(50% .11 115);--color-pear-700:oklch(40% .09 115);--color-pear-800:oklch(31% .07 115);--color-pear-900:oklch(23% .05 115);--color-emerald-200:oklch(93% .04 160);--color-emerald-300:oklch(80% .11 160);--color-emerald-400:oklch(68% .15 160);--color-emerald-500:oklch(54% .12 160);--color-emerald-600:oklch(49% .11 160);--color-emerald-700:oklch(40% .09 160);--color-emerald-800:oklch(31% .07 160);--color-emerald-900:oklch(23% .05 160);--color-pelorus-200:oklch(93% .04 205);--color-pelorus-300:oklch(80% .11 205);--color-pelorus-400:oklch(67% .15 205);--color-pelorus-500:oklch(53% .12 205);--color-pelorus-600:oklch(49% .11 205);--color-pelorus-700:oklch(39% .09 205);--color-pelorus-800:oklch(31% .07 205);--color-pelorus-900:oklch(23% .05 205);--color-azure-200:oklch(93% .04 250);--color-azure-300:oklch(81% .11 250);--color-azure-400:oklch(70% .15 250);--color-azure-500:oklch(55% .12 250);--color-azure-600:oklch(50% .11 250);--color-azure-700:oklch(41% .09 250);--color-azure-800:oklch(31% .07 250);--color-azure-900:oklch(23% .05 250);--color-violet-200:oklch(93% .04 295);--color-violet-300:oklch(82% .11 295);--color-violet-400:oklch(71% .15 295);--color-violet-500:oklch(56% .12 295);--color-violet-600:oklch(51% .11 295);--color-violet-700:oklch(41% .09 295);--color-violet-800:oklch(32% .07 295);--color-violet-900:oklch(24% .05 295);--color-byzantium-200:oklch(94% .04 340);--color-byzantium-300:oklch(83% .11 340);--color-byzantium-400:oklch(72% .15 340);--color-byzantium-500:oklch(57% .12 340);--color-byzantium-600:oklch(52% .11 340);--color-byzantium-700:oklch(42% .09 340);--color-byzantium-800:oklch(32% .07 340);--color-byzantium-900:oklch(24% .05 340)}@layer theme{:root,:host{--font-sans:"Open Sans", ui-sans-serif, system-ui, sans-serif;--font-mono:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;--color-red-300:oklch(80.8% .114 19.571);--color-red-500:oklch(63.7% .237 25.331);--color-emerald-300:oklch(84.5% .143 164.978);--color-emerald-500:oklch(69.6% .17 162.48);--color-violet-400:oklch(70.2% .183 293.541);--color-violet-500:oklch(60.6% .25 292.717);--color-gray-50:oklch(98.5% .002 247.839);--color-gray-100:oklch(96.7% .003 264.542);--color-gray-200:oklch(92.8% .006 264.531);--color-gray-400:oklch(70.7% .022 261.325);--color-gray-500:oklch(55.1% .027 264.364);--color-gray-600:oklch(44.6% .03 256.802);--color-gray-700:oklch(37.3% .034 259.733);--color-gray-800:oklch(27.8% .033 256.848);--color-black:#000;--color-white:#fff;--spacing:.25rem;--text-xs:.75rem;--text-xs--line-height:calc(1 / .75);--text-sm:.875rem;--text-sm--line-height:calc(1.25 / .875);--text-base:1rem;--text-base--line-height: 1.5 ;--text-lg:1.125rem;--text-lg--line-height:calc(1.75 / 1.125);--text-xl:1.25rem;--text-xl--line-height:calc(1.75 / 1.25);--text-2xl:1.5rem;--text-2xl--line-height:calc(2 / 1.5);--text-3xl:1.875rem;--text-3xl--line-height: 1.2 ;--font-weight-medium:500;--font-weight-semibold:600;--font-weight-bold:700;--tracking-wide:.025em;--default-transition-duration:.15s;--default-transition-timing-function:cubic-bezier(.4, 0, .2, 1);--default-font-family:var(--font-sans);--default-mono-font-family:var(--font-mono)}}@layer base{*,:after,:before,::backdrop{box-sizing:border-box;border:0 solid;margin:0;padding:0}::file-selector-button{box-sizing:border-box;border:0 solid;margin:0;padding:0}html,:host{-webkit-text-size-adjust:100%;-moz-tab-size:4;tab-size:4;line-height:1.5;font-family:var(--default-font-family,ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji");font-feature-settings:var(--default-font-feature-settings,normal);font-variation-settings:var(--default-font-variation-settings,normal);-webkit-tap-highlight-color:transparent}hr{height:0;color:inherit;border-top-width:1px}abbr:where([title]){-webkit-text-decoration:underline dotted;text-decoration:underline dotted}h1,h2,h3,h4,h5,h6{font-size:inherit;font-weight:inherit}a{color:inherit;-webkit-text-decoration:inherit;text-decoration:inherit}b,strong{font-weight:bolder}code,kbd,samp,pre{font-family:var(--default-mono-font-family,ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace);font-feature-settings:var(--default-mono-font-feature-settings,normal);font-variation-settings:var(--default-mono-font-variation-settings,normal);font-size:1em}small{font-size:80%}sub,sup{vertical-align:baseline;font-size:75%;line-height:0;position:relative}sub{bottom:-.25em}sup{top:-.5em}table{text-indent:0;border-color:inherit;border-collapse:collapse}:-moz-focusring{outline:auto}progress{vertical-align:baseline}summary{display:list-item}ol,ul,menu{list-style:none}img,svg,video,canvas,audio,iframe,embed,object{vertical-align:middle;display:block}img,video{max-width:100%;height:auto}button,input,select,optgroup,textarea{font:inherit;font-feature-settings:inherit;font-variation-settings:inherit;letter-spacing:inherit;color:inherit;opacity:1;background-color:#0000;border-radius:0}::file-selector-button{font:inherit;font-feature-settings:inherit;font-variation-settings:inherit;letter-spacing:inherit;color:inherit;opacity:1;background-color:#0000;border-radius:0}:where(select:is([multiple],[size])) optgroup{font-weight:bolder}:where(select:is([multiple],[size])) optgroup option{padding-inline-start:20px}::file-selector-button{margin-inline-end:4px}::placeholder{opacity:1}@supports (not ((-webkit-appearance:-apple-pay-button))) or (contain-intrinsic-size:1px){::placeholder{color:currentColor}@supports (color:color-mix(in lab,red,red)){::placeholder{color:color-mix(in oklab,currentcolor 50%,transparent)}}}textarea{resize:vertical}::-webkit-search-decoration{-webkit-appearance:none}::-webkit-date-and-time-value{min-height:1lh;text-align:inherit}::-webkit-datetime-edit{display:inline-flex}::-webkit-datetime-edit-fields-wrapper{padding:0}::-webkit-datetime-edit{padding-block:0}::-webkit-datetime-edit-year-field{padding-block:0}::-webkit-datetime-edit-month-field{padding-block:0}::-webkit-datetime-edit-day-field{padding-block:0}::-webkit-datetime-edit-hour-field{padding-block:0}::-webkit-datetime-edit-minute-field{padding-block:0}::-webkit-datetime-edit-second-field{padding-block:0}::-webkit-datetime-edit-millisecond-field{padding-block:0}::-webkit-datetime-edit-meridiem-field{padding-block:0}::-webkit-calendar-picker-indicator{line-height:1}:-moz-ui-invalid{box-shadow:none}button,input:where([type=button],[type=reset],[type=submit]){-webkit-appearance:button;-moz-appearance:button;appearance:button}::file-selector-button{-webkit-appearance:button;-moz-appearance:button;appearance:button}::-webkit-inner-spin-button{height:auto}::-webkit-outer-spin-button{height:auto}[hidden]:where(:not([hidden=until-found])){display:none!important}:root:not(span){overflow:var(--page-overflow)}:root{background:var(--page-scroll-bg,var(--root-bg));--page-scroll-bg-on:linear-gradient(var(--root-bg,#0000), var(--root-bg,#0000)) var(--root-bg,#0000)}@supports (color:color-mix(in lab,red,red)){:root{--page-scroll-bg-on:linear-gradient(var(--root-bg,#0000), var(--root-bg,#0000)) color-mix(in srgb, var(--root-bg,#0000), oklch(0% 0 0) calc(var(--page-has-backdrop,0) * 40%))}}:root{--page-scroll-transition-on:background-color .3s ease-out;transition:var(--page-scroll-transition);scrollbar-gutter:var(--page-scroll-gutter,unset);scrollbar-gutter:if(style(--page-has-scroll: 1): var(--page-scroll-gutter,unset) ; else: unset)}@keyframes set-page-has-scroll{0%,to{--page-has-scroll:1}}:root{--fx-noise:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'%3E%3Cfilter id='a'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='1.34' numOctaves='4' stitchTiles='stitch'%3E%3C/feTurbulence%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23a)' opacity='0.2'%3E%3C/rect%3E%3C/svg%3E")}:root,[data-theme]{background:var(--page-scroll-bg,var(--root-bg));color:var(--color-base-content)}:where(:root,[data-theme]){--root-bg:var(--color-base-100)}:root{scrollbar-color:currentColor #0000}@supports (color:color-mix(in lab,red,red)){:root{scrollbar-color:color-mix(in oklch,currentColor 35%,#0000) #0000}}@property --radialprogress{syntax:"<percentage>";inherits:true;initial-value:0%}:where(:root),:root:has(input.theme-controller[value=univention-light]:checked),[data-theme=univention-light]{color-scheme:light;--color-base-100:var(--color-white);--color-base-200:var(--color-gray-50);--color-base-300:var(--color-gray-100);--color-base-content:var(--color-black);--color-primary:var(--color-violet-500);--color-primary-content:var(--color-white);--color-secondary:var(--color-gray-200);--color-secondary-content:var(--color-gray-800);--color-accent:var(--color-violet-400);--color-accent-content:var(--color-white);--color-neutral:var(--color-gray-500);--color-neutral-content:var(--color-white);--color-info:var(--color-azure-300);--color-info-content:var(--color-white);--color-success:var(--color-emerald-300);--color-success-content:var(--color-white);--color-warning:var(--color-coral-300);--color-warning-content:var(--color-white);--color-error:var(--color-red-300);--color-error-content:var(--color-white);--radius-selector:.25rem;--radius-field:.25rem;--radius-box:.5rem;--border:1px;--depth:1;--noise:0}@media(prefers-color-scheme:dark){:root:not([data-theme]){color-scheme:dark;--color-base-100:var(--color-gray-700);--color-base-200:var(--color-gray-800);--color-base-300:var(--color-gray-700);--color-base-content:var(--color-white);--color-primary:var(--color-violet-400);--color-primary-content:var(--color-gray-800);--color-secondary:var(--color-gray-600);--color-secondary-content:var(--color-white);--color-accent:var(--color-violet-500);--color-accent-content:var(--color-white);--color-neutral:var(--color-gray-400);--color-neutral-content:var(--color-gray-800);--color-info:var(--color-azure-500);--color-info-content:var(--color-white);--color-success:var(--color-emerald-500);--color-success-content:var(--color-white);--color-warning:var(--color-coral-500);--color-warning-content:var(--color-white);--color-error:var(--color-red-500);--color-error-content:var(--color-white);--radius-selector:.25rem;--radius-field:.25rem;--radius-box:.5rem;--border:1px;--depth:1;--noise:0}}:root:has(input.theme-controller[value=univention-dark]:checked),[data-theme=univention-dark]{color-scheme:dark;--color-base-100:var(--color-gray-700);--color-base-200:var(--color-gray-800);--color-base-300:var(--color-gray-700);--color-base-content:var(--color-white);--color-primary:var(--color-violet-400);--color-primary-content:var(--color-gray-800);--color-secondary:var(--color-gray-600);--color-secondary-content:var(--color-white);--color-accent:var(--color-violet-500);--color-accent-content:var(--color-white);--color-neutral:var(--color-gray-400);--color-neutral-content:var(--color-gray-800);--color-info:var(--color-azure-500);--color-info-content:var(--color-white);--color-success:var(--color-emerald-500);--color-success-content:var(--color-white);--color-warning:var(--color-coral-500);--color-warning-content:var(--color-white);--color-error:var(--color-red-500);--color-error-content:var(--color-white);--radius-selector:.25rem;--radius-field:.25rem;--radius-box:.5rem;--border:1px;--depth:1;--noise:0}}@layer components;@layer utilities{@layer daisyui.l1.l2.l3{.diff{webkit-user-select:none;-webkit-user-select:none;user-select:none;direction:ltr;grid-template-rows:1fr 1.8rem 1fr;grid-template-columns:auto 1fr;width:100%;display:grid;position:relative;overflow:hidden;container-type:inline-size}.diff:focus-visible,.diff:has(.diff-item-1:focus-visible){outline-style:var(--tw-outline-style);outline-offset:1px;outline-width:2px;outline-color:var(--color-base-content)}.diff:focus-visible .diff-resizer{min-width:95cqi;max-width:95cqi}.diff:has(.diff-item-1:focus-visible){outline-style:var(--tw-outline-style);outline-offset:1px;outline-width:2px}.diff:has(.diff-item-1:focus-visible) .diff-resizer{min-width:5cqi;max-width:5cqi}@supports (-webkit-overflow-scrolling:touch) and (overflow:-webkit-paged-x){.diff:focus .diff-resizer{min-width:5cqi;max-width:5cqi}.diff:has(.diff-item-1:focus) .diff-resizer{min-width:95cqi;max-width:95cqi}}.modal{pointer-events:none;visibility:hidden;width:100%;max-width:none;height:100%;max-height:none;color:inherit;transition:visibility .3s allow-discrete,background-color .3s ease-out,opacity .1s ease-out;overscroll-behavior:contain;z-index:999;scrollbar-gutter:auto;background-color:#0000;place-items:center;margin:0;padding:0;display:grid;position:fixed;top:0;right:0;bottom:0;left:0;overflow:clip}.modal::backdrop{display:none}.fab{pointer-events:none;z-index:999;font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));white-space:nowrap;inset-inline-end:1rem;flex-direction:column-reverse;align-items:flex-end;gap:.5rem;display:flex;position:fixed;bottom:1rem}.fab>*{pointer-events:auto;align-items:center;gap:.5rem;display:flex}.fab>:hover,.fab>:has(:focus-visible){z-index:1}.fab>[tabindex]:first-child{transition-property:opacity,visibility,rotate;transition-duration:.2s;transition-timing-function:cubic-bezier(.4,0,.2,1);display:grid;position:relative}.fab .fab-close,.fab .fab-main-action{inset-inline-end:0;position:absolute;bottom:0}:is(.fab:focus-within:has(.fab-close),.fab:focus-within:has(.fab-main-action))>[tabindex]{opacity:0;rotate:90deg}.fab:focus-within>[tabindex]:first-child{pointer-events:none}.fab:focus-within>:nth-child(n+2){visibility:visible;--tw-scale-x:100%;--tw-scale-y:100%;--tw-scale-z:100%;scale:var(--tw-scale-x) var(--tw-scale-y);opacity:1}.fab>:nth-child(n+2){visibility:hidden;--tw-scale-x:80%;--tw-scale-y:80%;--tw-scale-z:80%;scale:var(--tw-scale-x) var(--tw-scale-y);opacity:0;transition-property:opacity,scale,visibility;transition-duration:.2s;transition-timing-function:cubic-bezier(.4,0,.2,1)}.fab>:nth-child(n+2).fab-main-action,.fab>:nth-child(n+2).fab-close{--tw-scale-x:100%;--tw-scale-y:100%;--tw-scale-z:100%;scale:var(--tw-scale-x) var(--tw-scale-y)}.fab>:nth-child(3){transition-delay:30ms}.fab>:nth-child(4){transition-delay:60ms}.fab>:nth-child(5){transition-delay:90ms}.fab>:nth-child(6){transition-delay:.12s}.tooltip{--tt-bg:var(--color-neutral);--tt-off: calc(100% + .5rem) ;--tt-tail: calc(100% + 1px + .25rem) ;display:inline-block;position:relative}.tooltip>.tooltip-content,.tooltip[data-tip]:before{border-radius:var(--radius-field);text-align:center;white-space:normal;max-width:20rem;color:var(--color-neutral-content);opacity:0;background-color:var(--tt-bg);pointer-events:none;z-index:2;--tw-content:attr(data-tip);content:var(--tw-content);width:max-content;padding-block:.25rem;padding-inline:.5rem;font-size:.875rem;line-height:1.25;position:absolute}.tooltip:after{opacity:0;background-color:var(--tt-bg);content:"";pointer-events:none;--mask-tooltip:url("data:image/svg+xml,%3Csvg width='10' height='4' viewBox='0 0 8 4' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0.500009 1C3.5 1 3.00001 4 5.00001 4C7 4 6.5 1 9.5 1C10 1 10 0.499897 10 0H0C-1.99338e-08 0.5 0 1 0.500009 1Z' fill='black'/%3E%3C/svg%3E%0A");width:.625rem;height:.25rem;-webkit-mask-position:-1px 0;mask-position:-1px 0;-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;-webkit-mask-image:var(--mask-tooltip);mask-image:var(--mask-tooltip);display:block;position:absolute}@media(prefers-reduced-motion:no-preference){.tooltip>.tooltip-content,.tooltip[data-tip]:before,.tooltip:after{transition:opacity .2s cubic-bezier(.4,0,.2,1) 75ms,transform .2s cubic-bezier(.4,0,.2,1) 75ms}}:is(.tooltip:is([data-tip]:not([data-tip=""]),:has(.tooltip-content:not(:empty))).tooltip-open,.tooltip:is([data-tip]:not([data-tip=""]),:has(.tooltip-content:not(:empty))):hover,.tooltip:is([data-tip]:not([data-tip=""]),:has(.tooltip-content:not(:empty))):has(:focus-visible))>.tooltip-content,:is(.tooltip:is([data-tip]:not([data-tip=""]),:has(.tooltip-content:not(:empty))).tooltip-open,.tooltip:is([data-tip]:not([data-tip=""]),:has(.tooltip-content:not(:empty))):hover,.tooltip:is([data-tip]:not([data-tip=""]),:has(.tooltip-content:not(:empty))):has(:focus-visible))[data-tip]:before,:is(.tooltip:is([data-tip]:not([data-tip=""]),:has(.tooltip-content:not(:empty))).tooltip-open,.tooltip:is([data-tip]:not([data-tip=""]),:has(.tooltip-content:not(:empty))):hover,.tooltip:is([data-tip]:not([data-tip=""]),:has(.tooltip-content:not(:empty))):has(:focus-visible)):after{opacity:1;--tt-pos:0rem}@media(prefers-reduced-motion:no-preference){:is(.tooltip:is([data-tip]:not([data-tip=""]),:has(.tooltip-content:not(:empty))).tooltip-open,.tooltip:is([data-tip]:not([data-tip=""]),:has(.tooltip-content:not(:empty))):hover,.tooltip:is([data-tip]:not([data-tip=""]),:has(.tooltip-content:not(:empty))):has(:focus-visible))>.tooltip-content,:is(.tooltip:is([data-tip]:not([data-tip=""]),:has(.tooltip-content:not(:empty))).tooltip-open,.tooltip:is([data-tip]:not([data-tip=""]),:has(.tooltip-content:not(:empty))):hover,.tooltip:is([data-tip]:not([data-tip=""]),:has(.tooltip-content:not(:empty))):has(:focus-visible))[data-tip]:before,:is(.tooltip:is([data-tip]:not([data-tip=""]),:has(.tooltip-content:not(:empty))).tooltip-open,.tooltip:is([data-tip]:not([data-tip=""]),:has(.tooltip-content:not(:empty))):hover,.tooltip:is([data-tip]:not([data-tip=""]),:has(.tooltip-content:not(:empty))):has(:focus-visible)):after{transition:opacity .2s cubic-bezier(.4,0,.2,1),transform .2s cubic-bezier(.4,0,.2,1)}}.tab{cursor:pointer;-webkit-appearance:none;-moz-appearance:none;appearance:none;text-align:center;webkit-user-select:none;-webkit-user-select:none;user-select:none;flex-wrap:wrap;justify-content:center;align-items:center;display:inline-flex;position:relative}@media(hover:hover){.tab:hover{color:var(--color-base-content)}}.tab{--tab-p:.75rem;--tab-bg:var(--color-base-100);--tab-border-color:var(--color-base-300);--tab-radius-ss:0;--tab-radius-se:0;--tab-radius-es:0;--tab-radius-ee:0;--tab-order:0;--tab-radius-min:calc(.75rem - var(--border));--tab-radius-limit:min(var(--radius-field), var(--tab-radius-min));--tab-radius-grad:#0000 calc(69% - var(--border)), var(--tab-border-color) calc(69% - var(--border) + .25px), var(--tab-border-color) 69%, var(--tab-bg) calc(69% + .25px) ;order:var(--tab-order);height:var(--tab-height);padding-inline:var(--tab-p);border-color:#0000;font-size:.875rem}.tab:is(input[type=radio]){min-width:fit-content}.tab:is(input[type=radio]):after{--tw-content:attr(aria-label);content:var(--tw-content)}.tab:is(label){position:relative}.tab:is(label) input{cursor:pointer;-webkit-appearance:none;-moz-appearance:none;appearance:none;opacity:0;position:absolute;top:0;right:0;bottom:0;left:0}:is(.tab:checked,.tab:is(label:has(:checked)),.tab:is(.tab-active,[aria-selected=true],[aria-current=true],[aria-current=page]))+.tab-content{display:block}.tab:not(:checked,label:has(:checked),:hover,.tab-active,[aria-selected=true],[aria-current=true],[aria-current=page]){color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.tab:not(:checked,label:has(:checked),:hover,.tab-active,[aria-selected=true],[aria-current=true],[aria-current=page]){color:color-mix(in oklab,var(--color-base-content) 50%,transparent)}}.tab:not(input):empty{cursor:default;flex-grow:1}.tab:focus{--tw-outline-style:none;outline-style:none}@media(forced-colors:active){.tab:focus{outline-offset:2px;outline:2px solid #0000}}.tab:focus-visible,.tab:is(label:has(:checked:focus-visible)){outline-offset:-5px;outline:2px solid}.tab[disabled]{pointer-events:none;opacity:.4}.menu{--menu-active-fg:var(--color-neutral-content);--menu-active-bg:var(--color-neutral);flex-flow:column wrap;width:fit-content;padding:.5rem;font-size:.875rem;display:flex}.menu :where(li ul){white-space:nowrap;margin-inline-start:1rem;padding-inline-start:.5rem;position:relative}.menu :where(li ul):before{background-color:var(--color-base-content);opacity:.1;width:var(--border);content:"";inset-inline-start:0;position:absolute;top:.75rem;bottom:.75rem}.menu :where(li>.menu-dropdown:not(.menu-dropdown-show)){display:none}.menu :where(li:not(.menu-title)>:not(ul,details,.menu-title,.btn)),.menu :where(li:not(.menu-title)>details>summary:not(.menu-title)){border-radius:var(--radius-field);text-align:start;text-wrap:balance;-webkit-user-select:none;user-select:none;grid-auto-columns:minmax(auto,max-content) auto max-content;grid-auto-flow:column;align-content:flex-start;align-items:center;gap:.5rem;padding-block:.375rem;padding-inline:.75rem;transition-property:color,background-color,box-shadow;transition-duration:.2s;transition-timing-function:cubic-bezier(0,0,.2,1);display:grid}.menu :where(li>details>summary){--tw-outline-style:none;outline-style:none}@media(forced-colors:active){.menu :where(li>details>summary){outline-offset:2px;outline:2px solid #0000}}.menu :where(li>details>summary)::-webkit-details-marker{display:none}:is(.menu :where(li>details>summary),.menu :where(li>.menu-dropdown-toggle)):after{content:"";transform-origin:50%;pointer-events:none;justify-self:flex-end;width:.375rem;height:.375rem;transition-property:rotate,translate;transition-duration:.2s;display:block;translate:0 -1px;rotate:-135deg;box-shadow:inset 2px 2px}.menu details{interpolate-size:allow-keywords;overflow:hidden}.menu details::details-content{block-size:0}@media(prefers-reduced-motion:no-preference){.menu details::details-content{transition-behavior:allow-discrete;transition-property:block-size,content-visibility;transition-duration:.2s;transition-timing-function:cubic-bezier(0,0,.2,1)}}.menu details[open]::details-content{block-size:auto}.menu :where(li>details[open]>summary):after,.menu :where(li>.menu-dropdown-toggle.menu-dropdown-show):after{translate:0 1px;rotate:45deg}.menu :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title),li:not(.menu-title,.disabled)>details>summary:not(.menu-title)):not(.menu-active,:active,.btn).menu-focus,.menu :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title),li:not(.menu-title,.disabled)>details>summary:not(.menu-title)):not(.menu-active,:active,.btn):focus-visible{cursor:pointer;background-color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.menu :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title),li:not(.menu-title,.disabled)>details>summary:not(.menu-title)):not(.menu-active,:active,.btn).menu-focus,.menu :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title),li:not(.menu-title,.disabled)>details>summary:not(.menu-title)):not(.menu-active,:active,.btn):focus-visible{background-color:color-mix(in oklab,var(--color-base-content) 10%,transparent)}}.menu :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title),li:not(.menu-title,.disabled)>details>summary:not(.menu-title)):not(.menu-active,:active,.btn).menu-focus,.menu :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title),li:not(.menu-title,.disabled)>details>summary:not(.menu-title)):not(.menu-active,:active,.btn):focus-visible{color:var(--color-base-content);--tw-outline-style:none;outline-style:none}@media(forced-colors:active){.menu :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title),li:not(.menu-title,.disabled)>details>summary:not(.menu-title)):not(.menu-active,:active,.btn).menu-focus,.menu :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title),li:not(.menu-title,.disabled)>details>summary:not(.menu-title)):not(.menu-active,:active,.btn):focus-visible{outline-offset:2px;outline:2px solid #0000}}.menu :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title):not(.menu-active,:active,.btn):hover,li:not(.menu-title,.disabled)>details>summary:not(.menu-title):not(.menu-active,:active,.btn):hover){cursor:pointer;background-color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.menu :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title):not(.menu-active,:active,.btn):hover,li:not(.menu-title,.disabled)>details>summary:not(.menu-title):not(.menu-active,:active,.btn):hover){background-color:color-mix(in oklab,var(--color-base-content) 10%,transparent)}}.menu :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title):not(.menu-active,:active,.btn):hover,li:not(.menu-title,.disabled)>details>summary:not(.menu-title):not(.menu-active,:active,.btn):hover){--tw-outline-style:none;outline-style:none}@media(forced-colors:active){.menu :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title):not(.menu-active,:active,.btn):hover,li:not(.menu-title,.disabled)>details>summary:not(.menu-title):not(.menu-active,:active,.btn):hover){outline-offset:2px;outline:2px solid #0000}}.menu :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title):not(.menu-active,:active,.btn):hover,li:not(.menu-title,.disabled)>details>summary:not(.menu-title):not(.menu-active,:active,.btn):hover){box-shadow:inset 0 1px #00000003,inset 0 -1px #ffffff03}.menu :where(li:empty){background-color:var(--color-base-content);opacity:.1;height:1px;margin:.5rem 1rem}.menu :where(li){flex-flow:column wrap;flex-shrink:0;align-items:stretch;display:flex;position:relative}.menu :where(li) .badge{justify-self:flex-end}.menu :where(li)>:not(ul,.menu-title,details,.btn):active,.menu :where(li)>:not(ul,.menu-title,details,.btn).menu-active,.menu :where(li)>details>summary:active{--tw-outline-style:none;outline-style:none}@media(forced-colors:active){.menu :where(li)>:not(ul,.menu-title,details,.btn):active,.menu :where(li)>:not(ul,.menu-title,details,.btn).menu-active,.menu :where(li)>details>summary:active{outline-offset:2px;outline:2px solid #0000}}.menu :where(li)>:not(ul,.menu-title,details,.btn):active,.menu :where(li)>:not(ul,.menu-title,details,.btn).menu-active,.menu :where(li)>details>summary:active{color:var(--menu-active-fg);background-color:var(--menu-active-bg);background-size:auto,calc(var(--noise) * 100%);background-image:none,var(--fx-noise)}:is(.menu :where(li)>:not(ul,.menu-title,details,.btn):active,.menu :where(li)>:not(ul,.menu-title,details,.btn).menu-active,.menu :where(li)>details>summary:active):not(:is(.menu :where(li)>:not(ul,.menu-title,details,.btn):active,.menu :where(li)>:not(ul,.menu-title,details,.btn).menu-active,.menu :where(li)>details>summary:active):active){box-shadow:0 2px calc(var(--depth) * 3px) -2px var(--menu-active-bg)}.menu :where(li).menu-disabled{pointer-events:none;color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.menu :where(li).menu-disabled{color:color-mix(in oklab,var(--color-base-content) 20%,transparent)}}.menu .dropdown:focus-within .menu-dropdown-toggle:after{translate:0 1px;rotate:45deg}.menu .dropdown-content{margin-top:.5rem;padding:.5rem}.menu .dropdown-content:before{display:none}.menu\\!{--menu-active-fg:var(--color-neutral-content)!important;--menu-active-bg:var(--color-neutral)!important;flex-flow:column wrap!important;width:fit-content!important;padding:.5rem!important;font-size:.875rem!important;display:flex!important}.menu\\! :where(li ul){white-space:nowrap!important;margin-inline-start:1rem!important;padding-inline-start:.5rem!important;position:relative!important}.menu\\! :where(li ul):before{background-color:var(--color-base-content)!important;opacity:.1!important;width:var(--border)!important;content:""!important;inset-inline-start:0!important;position:absolute!important;top:.75rem!important;bottom:.75rem!important}.menu\\! :where(li>.menu-dropdown:not(.menu-dropdown-show)){display:none!important}.menu\\! :where(li:not(.menu-title)>:not(ul,details,.menu-title,.btn)),.menu\\! :where(li:not(.menu-title)>details>summary:not(.menu-title)){border-radius:var(--radius-field)!important;text-align:start!important;text-wrap:balance!important;-webkit-user-select:none!important;user-select:none!important;grid-auto-columns:minmax(auto,max-content) auto max-content!important;grid-auto-flow:column!important;align-content:flex-start!important;align-items:center!important;gap:.5rem!important;padding-block:.375rem!important;padding-inline:.75rem!important;transition-property:color,background-color,box-shadow!important;transition-duration:.2s!important;transition-timing-function:cubic-bezier(0,0,.2,1)!important;display:grid!important}.menu\\! :where(li>details>summary){--tw-outline-style:none!important;outline-style:none!important}@media(forced-colors:active){.menu\\! :where(li>details>summary){outline-offset:2px!important;outline:2px solid #0000!important}}.menu\\! :where(li>details>summary)::-webkit-details-marker{display:none!important}:is(.menu\\! :where(li>details>summary),.menu\\! :where(li>.menu-dropdown-toggle)):after{content:""!important;transform-origin:50%!important;pointer-events:none!important;justify-self:flex-end!important;width:.375rem!important;height:.375rem!important;transition-property:rotate,translate!important;transition-duration:.2s!important;display:block!important;translate:0 -1px!important;rotate:-135deg!important;box-shadow:inset 2px 2px!important}.menu\\! details{interpolate-size:allow-keywords!important;overflow:hidden!important}.menu\\! details::details-content{block-size:0!important}@media(prefers-reduced-motion:no-preference){.menu\\! details::details-content{transition-behavior:allow-discrete!important;transition-property:block-size,content-visibility!important;transition-duration:.2s!important;transition-timing-function:cubic-bezier(0,0,.2,1)!important}}.menu\\! details[open]::details-content{block-size:auto!important}.menu\\! :where(li>details[open]>summary):after,.menu\\! :where(li>.menu-dropdown-toggle.menu-dropdown-show):after{translate:0 1px!important;rotate:45deg!important}.menu\\! :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title),li:not(.menu-title,.disabled)>details>summary:not(.menu-title)):not(.menu-active,:active,.btn).menu-focus,.menu\\! :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title),li:not(.menu-title,.disabled)>details>summary:not(.menu-title)):not(.menu-active,:active,.btn):focus-visible{cursor:pointer!important;background-color:var(--color-base-content)!important}@supports (color:color-mix(in lab,red,red)){.menu\\! :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title),li:not(.menu-title,.disabled)>details>summary:not(.menu-title)):not(.menu-active,:active,.btn).menu-focus,.menu\\! :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title),li:not(.menu-title,.disabled)>details>summary:not(.menu-title)):not(.menu-active,:active,.btn):focus-visible{background-color:color-mix(in oklab,var(--color-base-content) 10%,transparent)!important}}.menu\\! :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title),li:not(.menu-title,.disabled)>details>summary:not(.menu-title)):not(.menu-active,:active,.btn).menu-focus,.menu\\! :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title),li:not(.menu-title,.disabled)>details>summary:not(.menu-title)):not(.menu-active,:active,.btn):focus-visible{color:var(--color-base-content)!important;--tw-outline-style:none!important;outline-style:none!important}@media(forced-colors:active){.menu\\! :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title),li:not(.menu-title,.disabled)>details>summary:not(.menu-title)):not(.menu-active,:active,.btn).menu-focus,.menu\\! :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title),li:not(.menu-title,.disabled)>details>summary:not(.menu-title)):not(.menu-active,:active,.btn):focus-visible{outline-offset:2px!important;outline:2px solid #0000!important}}.menu\\! :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title):not(.menu-active,:active,.btn):hover,li:not(.menu-title,.disabled)>details>summary:not(.menu-title):not(.menu-active,:active,.btn):hover){cursor:pointer!important;background-color:var(--color-base-content)!important}@supports (color:color-mix(in lab,red,red)){.menu\\! :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title):not(.menu-active,:active,.btn):hover,li:not(.menu-title,.disabled)>details>summary:not(.menu-title):not(.menu-active,:active,.btn):hover){background-color:color-mix(in oklab,var(--color-base-content) 10%,transparent)!important}}.menu\\! :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title):not(.menu-active,:active,.btn):hover,li:not(.menu-title,.disabled)>details>summary:not(.menu-title):not(.menu-active,:active,.btn):hover){--tw-outline-style:none!important;outline-style:none!important}@media(forced-colors:active){.menu\\! :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title):not(.menu-active,:active,.btn):hover,li:not(.menu-title,.disabled)>details>summary:not(.menu-title):not(.menu-active,:active,.btn):hover){outline-offset:2px!important;outline:2px solid #0000!important}}.menu\\! :where(li:not(.menu-title,.disabled)>:not(ul,details,.menu-title):not(.menu-active,:active,.btn):hover,li:not(.menu-title,.disabled)>details>summary:not(.menu-title):not(.menu-active,:active,.btn):hover){box-shadow:inset 0 1px #00000003,inset 0 -1px #ffffff03!important}.menu\\! :where(li:empty){background-color:var(--color-base-content)!important;opacity:.1!important;height:1px!important;margin:.5rem 1rem!important}.menu\\! :where(li){flex-flow:column wrap!important;flex-shrink:0!important;align-items:stretch!important;display:flex!important;position:relative!important}.menu\\! :where(li) .badge{justify-self:flex-end!important}.menu\\! :where(li)>:not(ul,.menu-title,details,.btn):active,.menu\\! :where(li)>:not(ul,.menu-title,details,.btn).menu-active,.menu\\! :where(li)>details>summary:active{--tw-outline-style:none!important;outline-style:none!important}@media(forced-colors:active){.menu\\! :where(li)>:not(ul,.menu-title,details,.btn):active,.menu\\! :where(li)>:not(ul,.menu-title,details,.btn).menu-active,.menu\\! :where(li)>details>summary:active{outline-offset:2px!important;outline:2px solid #0000!important}}.menu\\! :where(li)>:not(ul,.menu-title,details,.btn):active,.menu\\! :where(li)>:not(ul,.menu-title,details,.btn).menu-active,.menu\\! :where(li)>details>summary:active{color:var(--menu-active-fg)!important;background-color:var(--menu-active-bg)!important;background-size:auto,calc(var(--noise) * 100%)!important;background-image:none,var(--fx-noise)!important}:is(.menu\\! :where(li)>:not(ul,.menu-title,details,.btn):active,.menu\\! :where(li)>:not(ul,.menu-title,details,.btn).menu-active,.menu\\! :where(li)>details>summary:active):not(:is(.menu\\! :where(li)>:not(ul,.menu-title,details,.btn):active,.menu\\! :where(li)>:not(ul,.menu-title,details,.btn).menu-active,.menu\\! :where(li)>details>summary:active):active){box-shadow:0 2px calc(var(--depth) * 3px) -2px var(--menu-active-bg)!important}.menu\\! :where(li).menu-disabled{pointer-events:none!important;color:var(--color-base-content)!important}@supports (color:color-mix(in lab,red,red)){.menu\\! :where(li).menu-disabled{color:color-mix(in oklab,var(--color-base-content) 20%,transparent)!important}}.menu\\! .dropdown:focus-within .menu-dropdown-toggle:after{translate:0 1px!important;rotate:45deg!important}.menu\\! .dropdown-content{margin-top:.5rem!important;padding:.5rem!important}.menu\\! .dropdown-content:before{display:none!important}.dock{z-index:1;background-color:var(--color-base-100);color:currentColor;border-top:.5px solid var(--color-base-content);flex-direction:row;justify-content:space-around;align-items:center;width:100%;padding:.5rem;display:flex;position:fixed;bottom:0;left:0;right:0}@supports (color:color-mix(in lab,red,red)){.dock{border-top:.5px solid color-mix(in oklab,var(--color-base-content) 5%,#0000)}}.dock{height:4rem;height:calc(4rem + env(safe-area-inset-bottom));padding-bottom:env(safe-area-inset-bottom)}.dock>*{cursor:pointer;border-radius:var(--radius-box);background-color:#0000;flex-direction:column;flex-shrink:1;flex-basis:100%;justify-content:center;align-items:center;gap:1px;max-width:8rem;height:100%;margin-bottom:.5rem;transition:opacity .2s ease-out;display:flex;position:relative}@media(hover:hover){.dock>:hover{opacity:.8}}:is(.dock>[aria-disabled=true],.dock>[disabled]),:is(.dock>[aria-disabled=true],.dock>[disabled]):hover{pointer-events:none;color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){:is(.dock>[aria-disabled=true],.dock>[disabled]),:is(.dock>[aria-disabled=true],.dock>[disabled]):hover{color:color-mix(in oklab,var(--color-base-content) 10%,transparent)}}:is(.dock>[aria-disabled=true],.dock>[disabled]),:is(.dock>[aria-disabled=true],.dock>[disabled]):hover{opacity:1}.dock>* .dock-label{font-size:.6875rem}.dock>:after{content:"";background-color:#0000;border-top:3px solid #0000;border-radius:3.40282e38px;width:1.5rem;height:.25rem;transition:background-color .1s ease-out,text-color .1s ease-out,width .1s ease-out;position:absolute;bottom:.2rem}.dropdown{position-area:var(--anchor-v,bottom) var(--anchor-h,span-right);display:inline-block;position:relative}.dropdown>:not(:has(~[class*=dropdown-content])):focus{--tw-outline-style:none;outline-style:none}@media(forced-colors:active){.dropdown>:not(:has(~[class*=dropdown-content])):focus{outline-offset:2px;outline:2px solid #0000}}.dropdown .dropdown-content{position:absolute}.dropdown.dropdown-close .dropdown-content,.dropdown:not(details,.dropdown-open,.dropdown-hover:hover,:focus-within) .dropdown-content,.dropdown.dropdown-hover:not(:hover) [tabindex]:first-child:focus:not(:focus-visible)~.dropdown-content{transform-origin:top;opacity:0;display:none;scale:.95}.dropdown[popover],.dropdown .dropdown-content{z-index:999}@media(prefers-reduced-motion:no-preference){.dropdown[popover],.dropdown .dropdown-content{transition-behavior:allow-discrete;transition-property:opacity,scale,display,overlay;transition-duration:.2s;transition-timing-function:cubic-bezier(.4,0,.2,1);animation:.2s dropdown}}@starting-style{.dropdown[popover],.dropdown .dropdown-content{opacity:0;scale:.95}}:is(.dropdown:not(.dropdown-close).dropdown-open,.dropdown:not(.dropdown-close):not(.dropdown-hover):focus,.dropdown:not(.dropdown-close):focus-within)>[tabindex]:first-child{pointer-events:none}:is(.dropdown:not(.dropdown-close).dropdown-open,.dropdown:not(.dropdown-close):not(.dropdown-hover):focus,.dropdown:not(.dropdown-close):focus-within) .dropdown-content,.dropdown:not(.dropdown-close).dropdown-hover:hover .dropdown-content{opacity:1;scale:1}.dropdown:is(details) summary::-webkit-details-marker{display:none}.dropdown:where([popover]){background:0 0}.dropdown[popover]{color:inherit;position:fixed}@supports not (position-area:bottom){.dropdown[popover]{margin:auto}.dropdown[popover].dropdown-close{transform-origin:top;opacity:0;display:none;scale:.95}.dropdown[popover].dropdown-open:not(:popover-open){transform-origin:top;opacity:0;display:none;scale:.95}.dropdown[popover]::backdrop{background-color:oklab(0% none none/.3)}}:is(.dropdown[popover].dropdown-close,.dropdown[popover]:not(.dropdown-open,:popover-open)){transform-origin:top;opacity:0;display:none;scale:.95}:where(.btn){width:unset}.btn{cursor:pointer;text-align:center;vertical-align:middle;outline-offset:2px;webkit-user-select:none;-webkit-user-select:none;user-select:none;padding-inline:var(--btn-p);color:var(--btn-fg);--tw-prose-links:var(--btn-fg);height:var(--size);font-size:var(--fontsize,.875rem);outline-color:var(--btn-color,var(--color-base-content));background-color:var(--btn-bg);background-size:auto,calc(var(--noise) * 100%);background-image:none,var(--btn-noise);border-width:var(--border);border-style:solid;border-color:var(--btn-border);text-shadow:0 .5px oklch(100% 0 0 / calc(var(--depth) * .15));touch-action:manipulation;box-shadow:0 .5px 0 .5px oklch(100% 0 0 / calc(var(--depth) * 6%)) inset,var(--btn-shadow);--size:calc(var(--size-field,.25rem) * 10);--btn-bg:var(--btn-color,var(--color-base-200));--btn-fg:var(--color-base-content);--btn-p:1rem;--btn-border:var(--btn-bg);border-start-start-radius:var(--join-ss,var(--radius-field));border-start-end-radius:var(--join-se,var(--radius-field));border-end-end-radius:var(--join-ee,var(--radius-field));border-end-start-radius:var(--join-es,var(--radius-field));flex-wrap:nowrap;flex-shrink:0;justify-content:center;align-items:center;gap:.375rem;font-weight:600;transition-property:color,background-color,border-color,box-shadow;transition-duration:.2s;transition-timing-function:cubic-bezier(0,0,.2,1);display:inline-flex}@supports (color:color-mix(in lab,red,red)){.btn{--btn-border:color-mix(in oklab, var(--btn-bg), #000 calc(var(--depth) * 5%))}}.btn{--btn-shadow:0 3px 2px -2px var(--btn-bg), 0 4px 3px -2px var(--btn-bg)}@supports (color:color-mix(in lab,red,red)){.btn{--btn-shadow:0 3px 2px -2px color-mix(in oklab, var(--btn-bg) calc(var(--depth) * 30%), #0000), 0 4px 3px -2px color-mix(in oklab, var(--btn-bg) calc(var(--depth) * 30%), #0000)}}.btn{--btn-noise:var(--fx-noise)}@media(hover:hover){.btn:hover{--btn-bg:var(--btn-color,var(--color-base-200))}@supports (color:color-mix(in lab,red,red)){.btn:hover{--btn-bg:color-mix(in oklab, var(--btn-color,var(--color-base-200)), #000 7%)}}}.btn:focus-visible,.btn:has(:focus-visible){isolation:isolate;outline-width:2px;outline-style:solid}.btn:active:not(.btn-active){--btn-bg:var(--btn-color,var(--color-base-200));translate:0 .5px}@supports (color:color-mix(in lab,red,red)){.btn:active:not(.btn-active){--btn-bg:color-mix(in oklab, var(--btn-color,var(--color-base-200)), #000 5%)}}.btn:active:not(.btn-active){--btn-border:var(--btn-color,var(--color-base-200))}@supports (color:color-mix(in lab,red,red)){.btn:active:not(.btn-active){--btn-border:color-mix(in oklab, var(--btn-color,var(--color-base-200)), #000 7%)}}.btn:active:not(.btn-active){--btn-shadow:0 0 0 0 oklch(0% 0 0/0), 0 0 0 0 oklch(0% 0 0/0)}.btn:is(input[type=checkbox],input[type=radio]){-webkit-appearance:none;-moz-appearance:none;appearance:none}.btn:is(input[type=checkbox],input[type=radio])[aria-label]:after{--tw-content:attr(aria-label);content:var(--tw-content)}.btn:where(input:checked:not(.filter .btn)){--btn-color:var(--color-primary);--btn-fg:var(--color-primary-content);isolation:isolate}.loading{pointer-events:none;aspect-ratio:1;vertical-align:middle;width:calc(var(--size-selector,.25rem) * 6);background-color:currentColor;display:inline-block;-webkit-mask-image:url("data:image/svg+xml,%3Csvg width='24' height='24' stroke='black' viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'%3E%3Cg transform-origin='center'%3E%3Ccircle cx='12' cy='12' r='9.5' fill='none' stroke-width='3' stroke-linecap='round'%3E%3CanimateTransform attributeName='transform' type='rotate' from='0 12 12' to='360 12 12' dur='2s' repeatCount='indefinite'/%3E%3Canimate attributeName='stroke-dasharray' values='0,150;42,150;42,150' keyTimes='0;0.475;1' dur='1.5s' repeatCount='indefinite'/%3E%3Canimate attributeName='stroke-dashoffset' values='0;-16;-59' keyTimes='0;0.475;1' dur='1.5s' repeatCount='indefinite'/%3E%3C/circle%3E%3C/g%3E%3C/svg%3E");mask-image:url("data:image/svg+xml,%3Csvg width='24' height='24' stroke='black' viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'%3E%3Cg transform-origin='center'%3E%3Ccircle cx='12' cy='12' r='9.5' fill='none' stroke-width='3' stroke-linecap='round'%3E%3CanimateTransform attributeName='transform' type='rotate' from='0 12 12' to='360 12 12' dur='2s' repeatCount='indefinite'/%3E%3Canimate attributeName='stroke-dasharray' values='0,150;42,150;42,150' keyTimes='0;0.475;1' dur='1.5s' repeatCount='indefinite'/%3E%3Canimate attributeName='stroke-dashoffset' values='0;-16;-59' keyTimes='0;0.475;1' dur='1.5s' repeatCount='indefinite'/%3E%3C/circle%3E%3C/g%3E%3C/svg%3E");-webkit-mask-position:50%;mask-position:50%;-webkit-mask-size:100%;mask-size:100%;-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat}.countdown{display:inline-flex}.countdown>*{visibility:hidden;--value-v: mod(max(0, var(--value)), 1000) ;--value-hundreds: round(to-zero, var(--value-v) / 100, 1) ;--value-tens: round(to-zero, mod(var(--value-v), 100) / 10, 1) ;--value-ones: mod(var(--value-v), 100) ;--show-hundreds:clamp(clamp(0, var(--digits,1) - 2, 1), var(--value-hundreds), 1);--show-tens:clamp(clamp(0, var(--digits,1) - 1, 1), var(--value-tens) + var(--show-hundreds), 1);--first-digits: round(to-zero, var(--value-v) / 10, 1) ;height:1em;width:calc(1ch + var(--show-tens) * 1ch + var(--show-hundreds) * 1ch);direction:ltr;transition:width .4s ease-out .2s;display:inline-block;position:relative;overflow-y:clip}.countdown>:before,.countdown>:after{visibility:visible;--tw-content:"00\\a 01\\a 02\\a 03\\a 04\\a 05\\a 06\\a 07\\a 08\\a 09\\a 10\\a 11\\a 12\\a 13\\a 14\\a 15\\a 16\\a 17\\a 18\\a 19\\a 20\\a 21\\a 22\\a 23\\a 24\\a 25\\a 26\\a 27\\a 28\\a 29\\a 30\\a 31\\a 32\\a 33\\a 34\\a 35\\a 36\\a 37\\a 38\\a 39\\a 40\\a 41\\a 42\\a 43\\a 44\\a 45\\a 46\\a 47\\a 48\\a 49\\a 50\\a 51\\a 52\\a 53\\a 54\\a 55\\a 56\\a 57\\a 58\\a 59\\a 60\\a 61\\a 62\\a 63\\a 64\\a 65\\a 66\\a 67\\a 68\\a 69\\a 70\\a 71\\a 72\\a 73\\a 74\\a 75\\a 76\\a 77\\a 78\\a 79\\a 80\\a 81\\a 82\\a 83\\a 84\\a 85\\a 86\\a 87\\a 88\\a 89\\a 90\\a 91\\a 92\\a 93\\a 94\\a 95\\a 96\\a 97\\a 98\\a 99\\a";content:var(--tw-content);font-variant-numeric:tabular-nums;white-space:pre;text-align:end;direction:rtl;transition:all 1s cubic-bezier(1,0,0,1),width .2s ease-out .2s,opacity .2s ease-out .2s;position:absolute;overflow-x:clip}.countdown>:before{width:calc(1ch + var(--show-hundreds) * 1ch);top:calc(var(--first-digits) * -1em);opacity:var(--show-tens);inset-inline-end:0}.countdown>:after{width:1ch;top:calc(var(--value-ones) * -1em);inset-inline-start:0}.collapse{border-radius:var(--radius-box,1rem);isolation:isolate;grid-template-rows:max-content 0fr;grid-template-columns:minmax(0,1fr);width:100%;display:grid;position:relative;overflow:hidden}@media(prefers-reduced-motion:no-preference){.collapse{transition:grid-template-rows .2s}}.collapse>input:is([type=checkbox],[type=radio]){-webkit-appearance:none;-moz-appearance:none;appearance:none;opacity:0;z-index:1;grid-row-start:1;grid-column-start:1;width:100%;min-height:1lh;padding:1rem;padding-inline-end:3rem;transition:background-color .2s ease-out}.collapse:is([open],[tabindex]:focus:not(.collapse-close),[tabindex]:focus-within:not(.collapse-close)),.collapse:not(.collapse-close):has(>input:is([type=checkbox],[type=radio]):checked){grid-template-rows:max-content 1fr}.collapse:is([open],[tabindex]:focus:not(.collapse-close),[tabindex]:focus-within:not(.collapse-close))>.collapse-content,.collapse:not(.collapse-close)>:where(input:is([type=checkbox],[type=radio]):checked~.collapse-content){content-visibility:visible;min-height:fit-content}@supports not (content-visibility:visible){.collapse:is([open],[tabindex]:focus:not(.collapse-close),[tabindex]:focus-within:not(.collapse-close))>.collapse-content,.collapse:not(.collapse-close)>:where(input:is([type=checkbox],[type=radio]):checked~.collapse-content){visibility:visible}}.collapse:focus-visible,.collapse:has(>input:is([type=checkbox],[type=radio]):focus-visible),.collapse:has(summary:focus-visible){outline-color:var(--color-base-content);outline-offset:2px;outline-width:2px;outline-style:solid}.collapse:not(.collapse-close)>input[type=checkbox],.collapse:not(.collapse-close)>input[type=radio]:not(:checked),.collapse:not(.collapse-close)>.collapse-title{cursor:pointer}:is(.collapse[tabindex]:focus:not(.collapse-close,.collapse[open]),.collapse[tabindex]:focus-within:not(.collapse-close,.collapse[open]))>.collapse-title{cursor:unset}.collapse:is([open],[tabindex]:focus:not(.collapse-close),[tabindex]:focus-within:not(.collapse-close))>:where(.collapse-content),.collapse:not(.collapse-close)>:where(input:is([type=checkbox],[type=radio]):checked~.collapse-content){padding-bottom:1rem}.collapse:is(details){width:100%}@media(prefers-reduced-motion:no-preference){.collapse:is(details)::details-content{transition:content-visibility .2s allow-discrete,visibility .2s allow-discrete,min-height .2s ease-out allow-discrete,padding .1s ease-out 20ms,background-color .2s ease-out,height .2s;interpolate-size:allow-keywords;height:0}.collapse:is(details):where([open])::details-content{height:auto}}.collapse:is(details) summary{display:block;position:relative}.collapse:is(details) summary::-webkit-details-marker{display:none}.collapse:is(details)>.collapse-content{content-visibility:visible}.collapse:is(details) summary{outline:none}.validator:user-valid{--input-color:var(--color-success)}.validator:user-valid:focus{--input-color:var(--color-success)}.validator:user-valid:checked{--input-color:var(--color-success)}.validator:user-valid[aria-checked=true]{--input-color:var(--color-success)}.validator:user-valid:focus-within{--input-color:var(--color-success)}.validator:has(:user-valid){--input-color:var(--color-success)}.validator:has(:user-valid):focus{--input-color:var(--color-success)}.validator:has(:user-valid):checked{--input-color:var(--color-success)}.validator:has(:user-valid)[aria-checked=true]{--input-color:var(--color-success)}.validator:has(:user-valid):focus-within{--input-color:var(--color-success)}.validator:user-invalid{--input-color:var(--color-error)}.validator:user-invalid:focus{--input-color:var(--color-error)}.validator:user-invalid:checked{--input-color:var(--color-error)}.validator:user-invalid[aria-checked=true]{--input-color:var(--color-error)}.validator:user-invalid:focus-within{--input-color:var(--color-error)}.validator:user-invalid~.validator-hint{visibility:visible;color:var(--color-error)}.validator:has(:user-invalid){--input-color:var(--color-error)}.validator:has(:user-invalid):focus{--input-color:var(--color-error)}.validator:has(:user-invalid):checked{--input-color:var(--color-error)}.validator:has(:user-invalid)[aria-checked=true]{--input-color:var(--color-error)}.validator:has(:user-invalid):focus-within{--input-color:var(--color-error)}.validator:has(:user-invalid)~.validator-hint{visibility:visible;color:var(--color-error)}:is(.validator[aria-invalid]:not([aria-invalid=false]),.validator:has([aria-invalid]:not([aria-invalid=false]))),:is(.validator[aria-invalid]:not([aria-invalid=false]),.validator:has([aria-invalid]:not([aria-invalid=false]))):focus,:is(.validator[aria-invalid]:not([aria-invalid=false]),.validator:has([aria-invalid]:not([aria-invalid=false]))):checked,:is(.validator[aria-invalid]:not([aria-invalid=false]),.validator:has([aria-invalid]:not([aria-invalid=false])))[aria-checked=true],:is(.validator[aria-invalid]:not([aria-invalid=false]),.validator:has([aria-invalid]:not([aria-invalid=false]))):focus-within{--input-color:var(--color-error)}:is(.validator[aria-invalid]:not([aria-invalid=false]),.validator:has([aria-invalid]:not([aria-invalid=false])))~.validator-hint{visibility:visible;color:var(--color-error)}.list{flex-direction:column;font-size:.875rem;display:flex}.list .list-row{--list-grid-cols:minmax(0, auto) 1fr;border-radius:var(--radius-box);word-break:break-word;grid-auto-flow:column;grid-template-columns:var(--list-grid-cols);gap:1rem;padding:1rem;display:grid;position:relative}:is(.list>:not(:last-child).list-row,.list>:not(:last-child) .list-row):after{content:"";border-bottom:var(--border) solid;inset-inline:var(--radius-box);border-color:var(--color-base-content);position:absolute;bottom:0}@supports (color:color-mix(in lab,red,red)){:is(.list>:not(:last-child).list-row,.list>:not(:last-child) .list-row):after{border-color:color-mix(in oklab,var(--color-base-content) 5%,transparent)}}.list\\!{flex-direction:column!important;font-size:.875rem!important;display:flex!important}.list\\! .list-row{--list-grid-cols:minmax(0, auto) 1fr!important;border-radius:var(--radius-box)!important;word-break:break-word!important;grid-auto-flow:column!important;grid-template-columns:var(--list-grid-cols)!important;gap:1rem!important;padding:1rem!important;display:grid!important;position:relative!important}:is(.list\\!>:not(:last-child).list-row,.list\\!>:not(:last-child) .list-row):after{content:""!important;border-bottom:var(--border) solid!important;inset-inline:var(--radius-box)!important;border-color:var(--color-base-content)!important;position:absolute!important;bottom:0!important}@supports (color:color-mix(in lab,red,red)){:is(.list\\!>:not(:last-child).list-row,.list\\!>:not(:last-child) .list-row):after{border-color:color-mix(in oklab,var(--color-base-content) 5%,transparent)!important}}.toast{translate:var(--toast-x,0) var(--toast-y,0);inset-inline:auto 1rem;background-color:#0000;flex-direction:column;gap:.5rem;width:max-content;max-width:calc(100vw - 2rem);display:flex;position:fixed;top:auto;bottom:1rem}@media(prefers-reduced-motion:no-preference){.toast>*{animation:.25s ease-out toast}}.toggle{border:var(--border) solid currentColor;color:var(--input-color);cursor:pointer;-webkit-appearance:none;-moz-appearance:none;appearance:none;vertical-align:middle;webkit-user-select:none;-webkit-user-select:none;user-select:none;--radius-selector-max:calc(var(--radius-selector) + var(--radius-selector) + var(--radius-selector));border-radius:calc(var(--radius-selector) + min(var(--toggle-p),var(--radius-selector-max)) + min(var(--border),var(--radius-selector-max)));padding:var(--toggle-p);flex-shrink:0;grid-template-columns:0fr 1fr 1fr;place-content:center;display:inline-grid;position:relative;box-shadow:inset 0 1px}@supports (color:color-mix(in lab,red,red)){.toggle{box-shadow:0 1px color-mix(in oklab,currentColor calc(var(--depth) * 10%),#0000) inset}}.toggle{--input-color:var(--color-base-content);transition:color .3s,grid-template-columns .2s}@supports (color:color-mix(in lab,red,red)){.toggle{--input-color:color-mix(in oklab, var(--color-base-content) 50%, #0000)}}.toggle{--toggle-p:calc(var(--size) * .125);--size:calc(var(--size-selector,.25rem) * 6);width:calc((var(--size) * 2) - (var(--border) + var(--toggle-p)) * 2);height:var(--size)}.toggle>*{z-index:1;cursor:pointer;-webkit-appearance:none;-moz-appearance:none;appearance:none;background-color:#0000;border:none;grid-column:2/span 1;grid-row-start:1;height:100%;padding:.125rem;transition:opacity .2s,rotate .4s}.toggle>:focus{--tw-outline-style:none;outline-style:none}@media(forced-colors:active){.toggle>:focus{outline-offset:2px;outline:2px solid #0000}}.toggle>:nth-child(2){color:var(--color-base-100);rotate:0deg}.toggle>:nth-child(3){color:var(--color-base-100);opacity:0;rotate:-15deg}.toggle:has(:checked)>:nth-child(2){opacity:0;rotate:15deg}.toggle:has(:checked)>:nth-child(3){opacity:1;rotate:0deg}.toggle:before{aspect-ratio:1;border-radius:var(--radius-selector);--tw-content:"";content:var(--tw-content);width:100%;height:100%;box-shadow:0 -1px oklch(0% 0 0 / calc(var(--depth) * .1)) inset,0 8px 0 -4px oklch(100% 0 0 / calc(var(--depth) * .1)) inset,0 1px currentColor;background-color:currentColor;grid-row-start:1;grid-column-start:2;transition:background-color .1s,translate .2s,inset-inline-start .2s;position:relative;inset-inline-start:0;translate:0}@supports (color:color-mix(in lab,red,red)){.toggle:before{box-shadow:0 -1px oklch(0% 0 0 / calc(var(--depth) * .1)) inset,0 8px 0 -4px oklch(100% 0 0 / calc(var(--depth) * .1)) inset,0 1px color-mix(in oklab,currentColor calc(var(--depth) * 10%),#0000)}}.toggle:before{background-size:auto,calc(var(--noise) * 100%);background-image:none,var(--fx-noise)}@media(forced-colors:active){.toggle:before{outline-style:var(--tw-outline-style);outline-offset:-1px;outline-width:1px}}@media print{.toggle:before{outline-offset:-1rem;outline:.25rem solid}}.toggle:focus-visible,.toggle:has(:focus-visible){outline-offset:2px;outline:2px solid}.toggle:checked,.toggle[aria-checked=true],.toggle:has(>input:checked){background-color:var(--color-base-100);--input-color:var(--color-base-content);grid-template-columns:1fr 1fr 0fr}:is(.toggle:checked,.toggle[aria-checked=true],.toggle:has(>input:checked)):before{background-color:currentColor}@starting-style{:is(.toggle:checked,.toggle[aria-checked=true],.toggle:has(>input:checked)):before{opacity:0}}.toggle:indeterminate{grid-template-columns:.5fr 1fr .5fr}.toggle:disabled{cursor:not-allowed;opacity:.3}.toggle:disabled:before{border:var(--border) solid currentColor;background-color:#0000}.input{cursor:text;border:var(--border) solid #0000;-webkit-appearance:none;-moz-appearance:none;appearance:none;background-color:var(--color-base-100);vertical-align:middle;white-space:nowrap;width:clamp(3rem,20rem,100%);height:var(--size);font-size:max(var(--font-size,.875rem),.875rem);touch-action:manipulation;border-color:var(--input-color);box-shadow:0 1px var(--input-color) inset,0 -1px oklch(100% 0 0 / calc(var(--depth) * .1)) inset;border-start-start-radius:var(--join-ss,var(--radius-field));border-start-end-radius:var(--join-se,var(--radius-field));border-end-end-radius:var(--join-ee,var(--radius-field));border-end-start-radius:var(--join-es,var(--radius-field));flex-shrink:1;align-items:center;gap:.5rem;padding-inline:.75rem;display:inline-flex;position:relative}@supports (color:color-mix(in lab,red,red)){.input{box-shadow:0 1px color-mix(in oklab,var(--input-color) calc(var(--depth) * 10%),#0000) inset,0 -1px oklch(100% 0 0 / calc(var(--depth) * .1)) inset}}.input{--size:calc(var(--size-field,.25rem) * 10);--input-color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.input{--input-color:color-mix(in oklab, var(--color-base-content) 20%, #0000)}}.input:where(input){display:inline-flex}.input :where(input){-webkit-appearance:none;-moz-appearance:none;appearance:none;background-color:#0000;border:none;width:100%;height:100%;display:inline-flex}.input :where(input):focus,.input :where(input):focus-within{--tw-outline-style:none;outline-style:none}@media(forced-colors:active){.input :where(input):focus,.input :where(input):focus-within{outline-offset:2px;outline:2px solid #0000}}.input :where(input[type=url]),.input :where(input[type=email]){direction:ltr}.input :where(input[type=date]){display:inline-flex}.input:focus,.input:focus-within{--input-color:var(--color-base-content);box-shadow:0 1px var(--input-color)}@supports (color:color-mix(in lab,red,red)){.input:focus,.input:focus-within{box-shadow:0 1px color-mix(in oklab,var(--input-color) calc(var(--depth) * 10%),#0000)}}.input:focus,.input:focus-within{outline:2px solid var(--input-color);outline-offset:2px;isolation:isolate}@media(pointer:coarse){@supports (-webkit-touch-callout:none){.input:focus,.input:focus-within{--font-size:1rem}}}.input:has(>input[disabled]),.input:is(:disabled,[disabled]),fieldset:disabled .input{cursor:not-allowed;border-color:var(--color-base-200);background-color:var(--color-base-200);color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.input:has(>input[disabled]),.input:is(:disabled,[disabled]),fieldset:disabled .input{color:color-mix(in oklab,var(--color-base-content) 40%,transparent)}}:is(.input:has(>input[disabled]),.input:is(:disabled,[disabled]),fieldset:disabled .input)::placeholder{color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){:is(.input:has(>input[disabled]),.input:is(:disabled,[disabled]),fieldset:disabled .input)::placeholder{color:color-mix(in oklab,var(--color-base-content) 20%,transparent)}}.input:has(>input[disabled]),.input:is(:disabled,[disabled]),fieldset:disabled .input{box-shadow:none}.input:has(>input[disabled])>input[disabled]{cursor:not-allowed}.input::-webkit-date-and-time-value{text-align:inherit}.input[type=number]::-webkit-inner-spin-button{margin-block:-.75rem;margin-inline-end:-.75rem}.input::-webkit-calendar-picker-indicator{position:absolute;inset-inline-end:.75em}.input:has(>input[type=date]) :where(input[type=date]){webkit-appearance:none;-webkit-appearance:none;-moz-appearance:none;appearance:none;display:inline-flex}.input:has(>input[type=date]) input[type=date]::-webkit-calendar-picker-indicator{cursor:pointer;width:1em;height:1em;position:absolute;inset-inline-end:.75em}.indicator{width:max-content;display:inline-flex;position:relative}.indicator :where(.indicator-item){z-index:1;white-space:nowrap;top:var(--indicator-t,0);bottom:var(--indicator-b,auto);left:var(--indicator-s,auto);right:var(--indicator-e,0);translate:var(--indicator-x,50%) var(--indicator-y,-50%);position:absolute}.table{border-collapse:separate;--tw-border-spacing-x: 0rem ;--tw-border-spacing-y: 0rem ;width:100%;border-spacing:var(--tw-border-spacing-x) var(--tw-border-spacing-y);border-radius:var(--radius-box);text-align:left;font-size:.875rem;position:relative}.table:where(:dir(rtl),[dir=rtl],[dir=rtl] *){text-align:right}@media(hover:hover){:is(.table tr.row-hover,.table tr.row-hover:nth-child(2n)):hover{background-color:var(--color-base-200)}}.table :where(th,td){vertical-align:middle;padding-block:.75rem;padding-inline:1rem}.table :where(thead,tfoot){white-space:nowrap;color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.table :where(thead,tfoot){color:color-mix(in oklab,var(--color-base-content) 60%,transparent)}}.table :where(thead,tfoot){font-size:.875rem;font-weight:600}.table :where(tfoot tr:first-child :is(td,th)){border-top:var(--border) solid var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.table :where(tfoot tr:first-child :is(td,th)){border-top:var(--border) solid color-mix(in oklch,var(--color-base-content) 5%,#0000)}}.table :where(.table-pin-rows thead tr){z-index:1;background-color:var(--color-base-100);position:sticky;top:0}.table :where(.table-pin-rows tfoot tr){z-index:1;background-color:var(--color-base-100);position:sticky;bottom:0}.table :where(.table-pin-cols tr th){background-color:var(--color-base-100);position:sticky;left:0;right:0}.table :where(thead tr :is(td,th),tbody tr:not(:last-child) :is(td,th)){border-bottom:var(--border) solid var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.table :where(thead tr :is(td,th),tbody tr:not(:last-child) :is(td,th)){border-bottom:var(--border) solid color-mix(in oklch,var(--color-base-content) 5%,#0000)}}.steps{counter-reset:step;grid-auto-columns:1fr;grid-auto-flow:column;display:inline-grid;overflow:auto hidden}.steps .step{text-align:center;--step-bg:var(--color-base-300);--step-fg:var(--color-base-content);grid-template-rows:40px 1fr;grid-template-columns:auto;place-items:center;min-width:4rem;display:grid}.steps .step:before{width:100%;height:.5rem;color:var(--step-bg);background-color:var(--step-bg);content:"";border:1px solid;grid-row-start:1;grid-column-start:1;margin-inline-start:-100%;top:0}.steps .step>.step-icon,.steps .step:not(:has(.step-icon)):after{--tw-content:counter(step);content:var(--tw-content);counter-increment:step;z-index:1;color:var(--step-fg);background-color:var(--step-bg);border:1px solid var(--step-bg);border-radius:3.40282e38px;grid-row-start:1;grid-column-start:1;place-self:center;place-items:center;width:2rem;height:2rem;display:grid;position:relative}.steps .step:first-child:before{--tw-content:none;content:var(--tw-content)}.steps .step[data-content]:after{--tw-content:attr(data-content);content:var(--tw-content)}.steps\\!{counter-reset:step!important;grid-auto-columns:1fr!important;grid-auto-flow:column!important;display:inline-grid!important;overflow:auto hidden!important}.steps\\! .step{text-align:center!important;--step-bg:var(--color-base-300)!important;--step-fg:var(--color-base-content)!important;grid-template-rows:40px 1fr!important;grid-template-columns:auto!important;place-items:center!important;min-width:4rem!important;display:grid!important}.steps\\! .step:before{width:100%!important;height:.5rem!important;color:var(--step-bg)!important;background-color:var(--step-bg)!important;content:""!important;border:1px solid!important;grid-row-start:1!important;grid-column-start:1!important;margin-inline-start:-100%!important;top:0!important}.steps\\! .step>.step-icon,.steps\\! .step:not(:has(.step-icon)):after{--tw-content:counter(step)!important;content:var(--tw-content)!important;counter-increment:step!important;z-index:1!important;color:var(--step-fg)!important;background-color:var(--step-bg)!important;border:1px solid var(--step-bg)!important;border-radius:3.40282e38px!important;grid-row-start:1!important;grid-column-start:1!important;place-self:center!important;place-items:center!important;width:2rem!important;height:2rem!important;display:grid!important;position:relative!important}.steps\\! .step:first-child:before{--tw-content:none!important;content:var(--tw-content)!important}.steps\\! .step[data-content]:after{--tw-content:attr(data-content)!important;content:var(--tw-content)!important}.range{-webkit-appearance:none;-moz-appearance:none;appearance:none;webkit-appearance:none;--range-thumb:var(--color-base-100);--range-thumb-size:calc(var(--size-selector,.25rem) * 6);--range-progress:currentColor;--range-fill:1;--range-p:.25rem;--range-bg:currentColor}@supports (color:color-mix(in lab,red,red)){.range{--range-bg:color-mix(in oklab, currentColor 10%, #0000)}}.range{cursor:pointer;vertical-align:middle;--radius-selector-max:calc(var(--radius-selector) + var(--radius-selector) + var(--radius-selector));border-radius:calc(var(--radius-selector) + min(var(--range-p),var(--radius-selector-max)));width:clamp(3rem,20rem,100%);height:var(--range-thumb-size);background-color:#0000;border:none;overflow:hidden}[dir=rtl] .range{--range-dir:-1}.range:focus{outline:none}.range:focus-visible{outline-offset:2px;outline:2px solid}.range::-webkit-slider-runnable-track{background-color:var(--range-bg);border-radius:var(--radius-selector);width:100%;height:calc(var(--range-thumb-size) * .5)}@media(forced-colors:active){.range::-webkit-slider-runnable-track{border:1px solid}.range::-moz-range-track{border:1px solid}}.range::-webkit-slider-thumb{box-sizing:border-box;border-radius:calc(var(--radius-selector) + min(var(--range-p),var(--radius-selector-max)));background-color:var(--range-thumb);height:var(--range-thumb-size);width:var(--range-thumb-size);border:var(--range-p) solid;-webkit-appearance:none;-moz-appearance:none;appearance:none;webkit-appearance:none;color:var(--range-progress);box-shadow:0 -1px oklch(0% 0 0 / calc(var(--depth) * .1)) inset,0 8px 0 -4px oklch(100% 0 0 / calc(var(--depth) * .1)) inset,0 1px currentColor,0 0 0 2rem var(--range-thumb) inset,calc((var(--range-dir,1) * -100cqw) - (var(--range-dir,1) * var(--range-thumb-size) / 2)) 0 0 calc(100cqw * var(--range-fill));position:relative;top:50%;transform:translateY(-50%)}@supports (color:color-mix(in lab,red,red)){.range::-webkit-slider-thumb{box-shadow:0 -1px oklch(0% 0 0 / calc(var(--depth) * .1)) inset,0 8px 0 -4px oklch(100% 0 0 / calc(var(--depth) * .1)) inset,0 1px color-mix(in oklab,currentColor calc(var(--depth) * 10%),#0000),0 0 0 2rem var(--range-thumb) inset,calc((var(--range-dir,1) * -100cqw) - (var(--range-dir,1) * var(--range-thumb-size) / 2)) 0 0 calc(100cqw * var(--range-fill))}}.range::-moz-range-track{background-color:var(--range-bg);border-radius:var(--radius-selector);width:100%;height:calc(var(--range-thumb-size) * .5)}.range::-moz-range-thumb{box-sizing:border-box;border-radius:calc(var(--radius-selector) + min(var(--range-p),var(--radius-selector-max)));height:var(--range-thumb-size);width:var(--range-thumb-size);border:var(--range-p) solid;color:var(--range-progress);box-shadow:0 -1px oklch(0% 0 0 / calc(var(--depth) * .1)) inset,0 8px 0 -4px oklch(100% 0 0 / calc(var(--depth) * .1)) inset,0 1px currentColor,0 0 0 2rem var(--range-thumb) inset,calc((var(--range-dir,1) * -100cqw) - (var(--range-dir,1) * var(--range-thumb-size) / 2)) 0 0 calc(100cqw * var(--range-fill));background-color:currentColor;position:relative;top:50%}@supports (color:color-mix(in lab,red,red)){.range::-moz-range-thumb{box-shadow:0 -1px oklch(0% 0 0 / calc(var(--depth) * .1)) inset,0 8px 0 -4px oklch(100% 0 0 / calc(var(--depth) * .1)) inset,0 1px color-mix(in oklab,currentColor calc(var(--depth) * 10%),#0000),0 0 0 2rem var(--range-thumb) inset,calc((var(--range-dir,1) * -100cqw) - (var(--range-dir,1) * var(--range-thumb-size) / 2)) 0 0 calc(100cqw * var(--range-fill))}}.range:disabled{cursor:not-allowed;opacity:.3}.select{border:var(--border) solid #0000;-webkit-appearance:none;-moz-appearance:none;appearance:none;background-color:var(--color-base-100);vertical-align:middle;width:clamp(3rem,20rem,100%);height:var(--size);touch-action:manipulation;white-space:nowrap;text-overflow:ellipsis;box-shadow:0 1px var(--input-color) inset,0 -1px oklch(100% 0 0 / calc(var(--depth) * .1)) inset;background-image:linear-gradient(45deg,#0000 50%,currentColor 50%),linear-gradient(135deg,currentColor 50%,#0000 50%);background-position:calc(100% - 20px) calc(1px + 50%),calc(100% - 16.1px) calc(1px + 50%);background-repeat:no-repeat;background-size:4px 4px,4px 4px;border-start-start-radius:var(--join-ss,var(--radius-field));border-start-end-radius:var(--join-se,var(--radius-field));border-end-end-radius:var(--join-ee,var(--radius-field));border-end-start-radius:var(--join-es,var(--radius-field));flex-shrink:1;align-items:center;gap:.375rem;padding-inline:.75rem 1.75rem;font-size:.875rem;display:inline-flex;position:relative;overflow:hidden}@supports (color:color-mix(in lab,red,red)){.select{box-shadow:0 1px color-mix(in oklab,var(--input-color) calc(var(--depth) * 10%),#0000) inset,0 -1px oklch(100% 0 0 / calc(var(--depth) * .1)) inset}}.select{border-color:var(--input-color);--input-color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.select{--input-color:color-mix(in oklab, var(--color-base-content) 20%, #0000)}}.select{--size:calc(var(--size-field,.25rem) * 10)}[dir=rtl] .select{background-position:12px calc(1px + 50%),16px calc(1px + 50%)}[dir=rtl] .select::picker(select){translate:.5rem}[dir=rtl] .select select::picker(select){translate:.5rem}.select[multiple]{background-image:none;height:auto;padding-block:.75rem;padding-inline-end:.75rem;overflow:auto}.select select{-webkit-appearance:none;-moz-appearance:none;appearance:none;width:calc(100% + 2.75rem);height:calc(100% - calc(var(--border) * 2));background:inherit;border-radius:inherit;border-style:none;align-items:center;margin-inline:-.75rem -1.75rem;padding-inline:.75rem 1.75rem}.select select:focus,.select select:focus-within{--tw-outline-style:none;outline-style:none}@media(forced-colors:active){.select select:focus,.select select:focus-within{outline-offset:2px;outline:2px solid #0000}}.select select:not(:last-child){background-image:none;margin-inline-end:-1.375rem}.select:focus,.select:focus-within{--input-color:var(--color-base-content);box-shadow:0 1px var(--input-color)}@supports (color:color-mix(in lab,red,red)){.select:focus,.select:focus-within{box-shadow:0 1px color-mix(in oklab,var(--input-color) calc(var(--depth) * 10%),#0000)}}.select:focus,.select:focus-within{outline:2px solid var(--input-color);outline-offset:2px;isolation:isolate}.select:has(>select[disabled]),.select:is(:disabled,[disabled]),fieldset:disabled .select{cursor:not-allowed;border-color:var(--color-base-200);background-color:var(--color-base-200);color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.select:has(>select[disabled]),.select:is(:disabled,[disabled]),fieldset:disabled .select{color:color-mix(in oklab,var(--color-base-content) 40%,transparent)}}:is(.select:has(>select[disabled]),.select:is(:disabled,[disabled]),fieldset:disabled .select)::placeholder{color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){:is(.select:has(>select[disabled]),.select:is(:disabled,[disabled]),fieldset:disabled .select)::placeholder{color:color-mix(in oklab,var(--color-base-content) 20%,transparent)}}.select:has(>select[disabled])>select[disabled]{cursor:not-allowed}@supports (appearance:base-select){.select,.select select{-webkit-appearance:base-select;-moz-appearance:base-select;appearance:base-select}:is(.select,.select select)::picker(select){-webkit-appearance:base-select;-moz-appearance:base-select;appearance:base-select}}:is(.select,.select select)::picker(select){color:inherit;border:var(--border) solid var(--color-base-200);border-radius:var(--radius-box);background-color:inherit;max-height:min(24rem,70dvh);box-shadow:0 2px calc(var(--depth) * 3px) -2px #0003;box-shadow:0 20px 25px -5px rgb(0 0 0/calc(var(--depth) * .1)),0 8px 10px -6px rgb(0 0 0/calc(var(--depth) * .1));margin-block:.5rem;margin-inline:.5rem;padding:.5rem;translate:-.5rem}:is(.select,.select select)::picker-icon{display:none}:is(.select,.select select) optgroup{padding-top:.5em}:is(.select,.select select) optgroup option:first-child{margin-top:.5em}:is(.select,.select select) option{border-radius:var(--radius-field);white-space:normal;padding-block:.375rem;padding-inline:.75rem;transition-property:color,background-color;transition-duration:.2s;transition-timing-function:cubic-bezier(0,0,.2,1)}:is(.select,.select select) option:not(:disabled):hover,:is(.select,.select select) option:not(:disabled):focus-visible{cursor:pointer;background-color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){:is(.select,.select select) option:not(:disabled):hover,:is(.select,.select select) option:not(:disabled):focus-visible{background-color:color-mix(in oklab,var(--color-base-content) 10%,transparent)}}:is(.select,.select select) option:not(:disabled):hover,:is(.select,.select select) option:not(:disabled):focus-visible{--tw-outline-style:none;outline-style:none}@media(forced-colors:active){:is(.select,.select select) option:not(:disabled):hover,:is(.select,.select select) option:not(:disabled):focus-visible{outline-offset:2px;outline:2px solid #0000}}:is(.select,.select select) option:not(:disabled):active{background-color:var(--color-neutral);color:var(--color-neutral-content);box-shadow:0 2px calc(var(--depth) * 3px) -2px var(--color-neutral)}.timeline{display:flex;position:relative}.timeline>li{grid-template-rows:var(--timeline-row-start,minmax(0, 1fr)) auto var(--timeline-row-end,minmax(0, 1fr));grid-template-columns:var(--timeline-col-start,minmax(0, 1fr)) auto var(--timeline-col-end,minmax(0, 1fr));flex-shrink:0;align-items:center;display:grid;position:relative}.timeline>li>hr{border:none;width:100%}.timeline>li>hr:first-child{grid-row-start:2;grid-column-start:1}.timeline>li>hr:last-child{grid-area:2/3/auto/none}@media print{.timeline>li>hr{border:.1px solid var(--color-base-300)}}.timeline :where(hr){background-color:var(--color-base-300);height:.25rem}.timeline:has(.timeline-middle hr):first-child{border-start-start-radius:0;border-start-end-radius:var(--radius-selector);border-end-end-radius:var(--radius-selector);border-end-start-radius:0}.timeline:has(.timeline-middle hr):last-child,.timeline:not(:has(.timeline-middle)) :first-child hr:last-child{border-start-start-radius:var(--radius-selector);border-start-end-radius:0;border-end-end-radius:0;border-end-start-radius:var(--radius-selector)}.timeline:not(:has(.timeline-middle)) :last-child hr:first-child{border-start-start-radius:0;border-start-end-radius:var(--radius-selector);border-end-end-radius:var(--radius-selector);border-end-start-radius:0}.swap{cursor:pointer;vertical-align:middle;webkit-user-select:none;-webkit-user-select:none;user-select:none;place-content:center;display:inline-grid;position:relative}.swap input{-webkit-appearance:none;-moz-appearance:none;appearance:none;border:none}.swap>*{grid-row-start:1;grid-column-start:1}@media(prefers-reduced-motion:no-preference){.swap>*{transition-property:transform,rotate,opacity;transition-duration:.2s;transition-timing-function:cubic-bezier(0,0,.2,1)}}.swap .swap-on,.swap .swap-indeterminate,.swap input:indeterminate~.swap-on,.swap input:is(:checked,:indeterminate)~.swap-off{opacity:0}.swap input:checked~.swap-on,.swap input:indeterminate~.swap-indeterminate{opacity:1;backface-visibility:visible}.avatar{vertical-align:middle;display:inline-flex;position:relative}.avatar>div{aspect-ratio:1;display:block;overflow:hidden}.avatar img{object-fit:cover;width:100%;height:100%}.checkbox{border:var(--border) solid var(--input-color,var(--color-base-content))}@supports (color:color-mix(in lab,red,red)){.checkbox{border:var(--border) solid var(--input-color,color-mix(in oklab, var(--color-base-content) 20%, #0000))}}.checkbox{cursor:pointer;-webkit-appearance:none;-moz-appearance:none;appearance:none;border-radius:var(--radius-selector);vertical-align:middle;color:var(--color-base-content);box-shadow:0 1px oklch(0% 0 0 / calc(var(--depth) * .1)) inset,0 0 #0000 inset,0 0 #0000;--size:calc(var(--size-selector,.25rem) * 6);width:var(--size);height:var(--size);background-size:auto,calc(var(--noise) * 100%);background-image:none,var(--fx-noise);flex-shrink:0;padding:.25rem;transition:background-color .2s,box-shadow .2s;display:inline-block;position:relative}.checkbox:before{--tw-content:"";content:var(--tw-content);opacity:0;clip-path:polygon(20% 100%,20% 80%,50% 80%,50% 80%,70% 80%,70% 100%);width:100%;height:100%;box-shadow:0 3px oklch(100% 0 0 / calc(var(--depth) * .1)) inset;background-color:currentColor;font-size:1rem;line-height:.75;transition:clip-path .3s .1s,opacity .1s .1s,rotate .3s .1s,translate .3s .1s;display:block;rotate:45deg}.checkbox:focus-visible{outline:2px solid var(--input-color,currentColor);outline-offset:2px}.checkbox:checked,.checkbox[aria-checked=true]{background-color:var(--input-color,#0000);box-shadow:0 0 #0000 inset,0 8px 0 -4px oklch(100% 0 0 / calc(var(--depth) * .1)) inset,0 1px oklch(0% 0 0 / calc(var(--depth) * .1))}:is(.checkbox:checked,.checkbox[aria-checked=true]):before{clip-path:polygon(20% 100%,20% 80%,50% 80%,50% 0%,70% 0%,70% 100%);opacity:1}@media(forced-colors:active){:is(.checkbox:checked,.checkbox[aria-checked=true]):before{--tw-content:"✔︎";clip-path:none;background-color:#0000;rotate:0deg}}@media print{:is(.checkbox:checked,.checkbox[aria-checked=true]):before{--tw-content:"✔︎";clip-path:none;background-color:#0000;rotate:0deg}}.checkbox:indeterminate{background-color:var(--input-color,var(--color-base-content))}@supports (color:color-mix(in lab,red,red)){.checkbox:indeterminate{background-color:var(--input-color,color-mix(in oklab, var(--color-base-content) 20%, #0000))}}.checkbox:indeterminate:before{opacity:1;clip-path:polygon(20% 100%,20% 80%,50% 80%,50% 80%,80% 80%,80% 100%);translate:0 -35%;rotate:0deg}.radio{cursor:pointer;-webkit-appearance:none;-moz-appearance:none;appearance:none;vertical-align:middle;border:var(--border) solid var(--input-color,currentColor);border-radius:3.40282e38px;flex-shrink:0;padding:.25rem;display:inline-block;position:relative}@supports (color:color-mix(in lab,red,red)){.radio{border:var(--border) solid var(--input-color,color-mix(in srgb, currentColor 20%, #0000))}}.radio{box-shadow:0 1px oklch(0% 0 0 / calc(var(--depth) * .1)) inset;--size:calc(var(--size-selector,.25rem) * 6);width:var(--size);height:var(--size);color:var(--input-color,currentColor)}.radio:before{--tw-content:"";content:var(--tw-content);background-size:auto,calc(var(--noise) * 100%);background-image:none,var(--fx-noise);border-radius:3.40282e38px;width:100%;height:100%;display:block}.radio:focus-visible{outline:2px solid}.radio:checked,.radio[aria-checked=true]{background-color:var(--color-base-100);border-color:currentColor}@media(prefers-reduced-motion:no-preference){.radio:checked,.radio[aria-checked=true]{animation:.2s ease-out radio}}:is(.radio:checked,.radio[aria-checked=true]):before{box-shadow:0 -1px oklch(0% 0 0 / calc(var(--depth) * .1)) inset,0 8px 0 -4px oklch(100% 0 0 / calc(var(--depth) * .1)) inset,0 1px oklch(0% 0 0 / calc(var(--depth) * .1));background-color:currentColor}@media(forced-colors:active){:is(.radio:checked,.radio[aria-checked=true]):before{outline-style:var(--tw-outline-style);outline-offset:-1px;outline-width:1px}}@media print{:is(.radio:checked,.radio[aria-checked=true]):before{outline-offset:-1rem;outline:.25rem solid}}.rating{vertical-align:middle;display:inline-flex;position:relative}.rating input{-webkit-appearance:none;-moz-appearance:none;appearance:none;border:none}.rating :where(*){background-color:var(--color-base-content);opacity:.2;border-radius:0;width:1.5rem;height:1.5rem}@media(prefers-reduced-motion:no-preference){.rating :where(*){animation:.25s ease-out rating}}.rating :where(*):is(input){cursor:pointer}.rating .rating-hidden{background-color:#0000;width:.5rem}.rating input[type=radio]:checked{background-image:none}.rating :checked,.rating [aria-checked=true],.rating [aria-current=true],.rating :has(~:checked,~[aria-checked=true],~[aria-current=true]){opacity:1}.rating :focus-visible{scale:1.1}@media(prefers-reduced-motion:no-preference){.rating :focus-visible{transition:scale .2s ease-out}}.rating :active:focus{animation:none;scale:1.1}.rating\\!{vertical-align:middle!important;display:inline-flex!important;position:relative!important}.rating\\! input{-webkit-appearance:none!important;-moz-appearance:none!important;appearance:none!important;border:none!important}.rating\\! :where(*){background-color:var(--color-base-content)!important;opacity:.2!important;border-radius:0!important;width:1.5rem!important;height:1.5rem!important}@media(prefers-reduced-motion:no-preference){.rating\\! :where(*){animation:.25s ease-out rating!important}}.rating\\! :where(*):is(input){cursor:pointer!important}.rating\\! .rating-hidden{background-color:#0000!important;width:.5rem!important}.rating\\! input[type=radio]:checked{background-image:none!important}.rating\\! :checked,.rating\\! [aria-checked=true],.rating\\! [aria-current=true],.rating\\! :has(~:checked,~[aria-checked=true],~[aria-current=true]){opacity:1!important}.rating\\! :focus-visible{scale:1.1!important}@media(prefers-reduced-motion:no-preference){.rating\\! :focus-visible{transition:scale .2s ease-out!important}}.rating\\! :active:focus{animation:none!important;scale:1.1!important}.navbar{align-items:center;width:100%;min-height:4rem;padding:.5rem;display:flex}.drawer{grid-auto-columns:max-content auto;width:100%;display:grid;position:relative}.card{border-radius:var(--radius-box);outline-offset:2px;outline:0 solid #0000;flex-direction:column;transition:outline .2s ease-in-out;display:flex;position:relative}.card:focus{--tw-outline-style:none;outline-style:none}@media(forced-colors:active){.card:focus{outline-offset:2px;outline:2px solid #0000}}.card:focus-visible{outline-color:currentColor}.card :where(figure:first-child){border-start-start-radius:inherit;border-start-end-radius:inherit;border-end-end-radius:unset;border-end-start-radius:unset;overflow:hidden}.card :where(figure:last-child){border-start-start-radius:unset;border-start-end-radius:unset;border-end-end-radius:inherit;border-end-start-radius:inherit;overflow:hidden}.card figure{justify-content:center;align-items:center;display:flex}.card:has(>input:is(input[type=checkbox],input[type=radio])){cursor:pointer;-webkit-user-select:none;user-select:none}.card:has(>:checked){outline:2px solid}.stats{border-radius:var(--radius-box);grid-auto-flow:column;display:inline-grid;position:relative;overflow-x:auto}.progress{-webkit-appearance:none;-moz-appearance:none;appearance:none;border-radius:var(--radius-box);background-color:currentColor;width:100%;height:.5rem;position:relative;overflow:hidden}@supports (color:color-mix(in lab,red,red)){.progress{background-color:color-mix(in oklab,currentcolor 20%,transparent)}}.progress{color:var(--color-base-content)}.progress:indeterminate{background-image:repeating-linear-gradient(90deg,currentColor -1% 10%,#0000 10% 90%);background-position-x:15%;background-size:200%}@media(prefers-reduced-motion:no-preference){.progress:indeterminate{animation:5s ease-in-out infinite progress}}@supports ((-moz-appearance:none)){.progress:indeterminate::-moz-progress-bar{background-color:#0000}@media(prefers-reduced-motion:no-preference){.progress:indeterminate::-moz-progress-bar{background-image:repeating-linear-gradient(90deg,currentColor -1% 10%,#0000 10% 90%);background-position-x:15%;background-size:200%;animation:5s ease-in-out infinite progress}}.progress::-moz-progress-bar{border-radius:var(--radius-box);background-color:currentColor}}@supports ((-webkit-appearance:none)){.progress::-webkit-progress-bar{border-radius:var(--radius-box);background-color:#0000}.progress::-webkit-progress-value{border-radius:var(--radius-box);background-color:currentColor}}.file-input{cursor:pointer;border:var(--border) solid #0000;-webkit-appearance:none;-moz-appearance:none;appearance:none;background-color:var(--color-base-100);vertical-align:middle;webkit-user-select:none;-webkit-user-select:none;user-select:none;width:clamp(3rem,20rem,100%);height:var(--size);border-color:var(--input-color);box-shadow:0 1px var(--input-color) inset,0 -1px oklch(100% 0 0 / calc(var(--depth) * .1)) inset;border-start-start-radius:var(--join-ss,var(--radius-field));border-start-end-radius:var(--join-se,var(--radius-field));border-end-end-radius:var(--join-ee,var(--radius-field));border-end-start-radius:var(--join-es,var(--radius-field));align-items:center;padding-inline-end:.75rem;font-size:.875rem;line-height:2;display:inline-flex}@supports (color:color-mix(in lab,red,red)){.file-input{box-shadow:0 1px color-mix(in oklab,var(--input-color) calc(var(--depth) * 10%),#0000) inset,0 -1px oklch(100% 0 0 / calc(var(--depth) * .1)) inset}}.file-input{--size:calc(var(--size-field,.25rem) * 10);--input-color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.file-input{--input-color:color-mix(in oklab, var(--color-base-content) 20%, #0000)}}.file-input::file-selector-button{cursor:pointer;webkit-user-select:none;-webkit-user-select:none;user-select:none;height:calc(100% + var(--border) * 2);margin-inline-end:1rem;margin-block:calc(var(--border) * -1);color:var(--btn-fg);border-width:var(--border);border-style:solid;border-color:var(--btn-border);background-color:var(--btn-bg);background-size:calc(var(--noise) * 100%);background-image:var(--btn-noise);text-shadow:0 .5px oklch(1 0 0 / calc(var(--depth) * .15));box-shadow:0 .5px 0 .5px #fff inset,var(--btn-shadow);border-start-start-radius:calc(var(--join-ss,var(--radius-field) - var(--border)));border-end-start-radius:calc(var(--join-es,var(--radius-field) - var(--border)));margin-inline-start:calc(var(--border) * -1);padding-inline:1rem;font-size:.875rem;font-weight:600}@supports (color:color-mix(in lab,red,red)){.file-input::file-selector-button{box-shadow:0 .5px 0 .5px color-mix(in oklab,color-mix(in oklab,white 30%,var(--btn-bg)) calc(var(--depth) * 20%),#0000) inset,var(--btn-shadow)}}.file-input::file-selector-button{--size:calc(var(--size-field,.25rem) * 10);--btn-bg:var(--btn-color,var(--color-base-200));--btn-fg:var(--color-base-content);--btn-border:var(--btn-bg)}@supports (color:color-mix(in lab,red,red)){.file-input::file-selector-button{--btn-border:color-mix(in oklab, var(--btn-bg), #000 5%)}}.file-input::file-selector-button{--btn-shadow:0 3px 2px -2px var(--btn-bg), 0 4px 3px -2px var(--btn-bg)}@supports (color:color-mix(in lab,red,red)){.file-input::file-selector-button{--btn-shadow:0 3px 2px -2px color-mix(in oklab, var(--btn-bg) 30%, #0000), 0 4px 3px -2px color-mix(in oklab, var(--btn-bg) 30%, #0000)}}.file-input::file-selector-button{--btn-noise:var(--fx-noise)}.file-input:focus{--input-color:var(--color-base-content);box-shadow:0 1px var(--input-color)}@supports (color:color-mix(in lab,red,red)){.file-input:focus{box-shadow:0 1px color-mix(in oklab,var(--input-color) 10%,#0000)}}.file-input:focus{outline:2px solid var(--input-color);outline-offset:2px;isolation:isolate}.file-input:has(>input[disabled]),.file-input:is(:disabled,[disabled]){cursor:not-allowed;border-color:var(--color-base-200);background-color:var(--color-base-200)}:is(.file-input:has(>input[disabled]),.file-input:is(:disabled,[disabled]))::placeholder{color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){:is(.file-input:has(>input[disabled]),.file-input:is(:disabled,[disabled]))::placeholder{color:color-mix(in oklab,var(--color-base-content) 20%,transparent)}}.file-input:has(>input[disabled]),.file-input:is(:disabled,[disabled]){box-shadow:none;color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.file-input:has(>input[disabled]),.file-input:is(:disabled,[disabled]){color:color-mix(in oklch,var(--color-base-content) 20%,#0000)}}:is(.file-input:has(>input[disabled]),.file-input:is(:disabled,[disabled]))::file-selector-button{cursor:not-allowed;border-color:var(--color-base-200);background-color:var(--color-base-200);--btn-border:#0000;--btn-noise:none;--btn-fg:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){:is(.file-input:has(>input[disabled]),.file-input:is(:disabled,[disabled]))::file-selector-button{--btn-fg:color-mix(in oklch, var(--color-base-content) 20%, #0000)}}.textarea{border:var(--border) solid #0000;-webkit-appearance:none;-moz-appearance:none;appearance:none;border-radius:var(--radius-field);background-color:var(--color-base-100);vertical-align:middle;width:clamp(3rem,20rem,100%);min-height:5rem;font-size:max(var(--font-size,.875rem),.875rem);touch-action:manipulation;border-color:var(--input-color);box-shadow:0 1px var(--input-color) inset,0 -1px oklch(100% 0 0 / calc(var(--depth) * .1)) inset;flex-shrink:1;padding-block:.5rem;padding-inline:.75rem}@supports (color:color-mix(in lab,red,red)){.textarea{box-shadow:0 1px color-mix(in oklab,var(--input-color) calc(var(--depth) * 10%),#0000) inset,0 -1px oklch(100% 0 0 / calc(var(--depth) * .1)) inset}}.textarea{--input-color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.textarea{--input-color:color-mix(in oklab, var(--color-base-content) 20%, #0000)}}.textarea textarea{-webkit-appearance:none;-moz-appearance:none;appearance:none;background-color:#0000;border:none}.textarea textarea:focus,.textarea textarea:focus-within{--tw-outline-style:none;outline-style:none}@media(forced-colors:active){.textarea textarea:focus,.textarea textarea:focus-within{outline-offset:2px;outline:2px solid #0000}}.textarea:focus,.textarea:focus-within{--input-color:var(--color-base-content);box-shadow:0 1px var(--input-color)}@supports (color:color-mix(in lab,red,red)){.textarea:focus,.textarea:focus-within{box-shadow:0 1px color-mix(in oklab,var(--input-color) calc(var(--depth) * 10%),#0000)}}.textarea:focus,.textarea:focus-within{outline:2px solid var(--input-color);outline-offset:2px;isolation:isolate}@media(pointer:coarse){@supports (-webkit-touch-callout:none){.textarea:focus,.textarea:focus-within{--font-size:1rem}}}.textarea:has(>textarea[disabled]),.textarea:is(:disabled,[disabled]){cursor:not-allowed;border-color:var(--color-base-200);background-color:var(--color-base-200);color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.textarea:has(>textarea[disabled]),.textarea:is(:disabled,[disabled]){color:color-mix(in oklab,var(--color-base-content) 40%,transparent)}}:is(.textarea:has(>textarea[disabled]),.textarea:is(:disabled,[disabled]))::placeholder{color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){:is(.textarea:has(>textarea[disabled]),.textarea:is(:disabled,[disabled]))::placeholder{color:color-mix(in oklab,var(--color-base-content) 20%,transparent)}}.textarea:has(>textarea[disabled]),.textarea:is(:disabled,[disabled]){box-shadow:none}.textarea:has(>textarea[disabled])>textarea[disabled]{cursor:not-allowed}.stack{grid-template-rows:3px 4px 1fr 4px 3px;grid-template-columns:3px 4px 1fr 4px 3px;display:inline-grid}.stack>*{width:100%;height:100%}.stack>:nth-child(n+2){opacity:.7;width:100%}.stack>:nth-child(2){z-index:2;opacity:.9}.stack>:first-child{z-index:3;width:100%}.hero{background-position:50%;background-size:cover;place-items:center;width:100%;display:grid}.hero>*{grid-row-start:1;grid-column-start:1}.divider{white-space:nowrap;height:1rem;margin:var(--divider-m,1rem 0);--divider-color:var(--color-base-content);flex-direction:row;align-self:stretch;align-items:center;display:flex}@supports (color:color-mix(in lab,red,red)){.divider{--divider-color:color-mix(in oklab, var(--color-base-content) 10%, transparent)}}.divider:before,.divider:after{content:"";background-color:var(--divider-color);flex-grow:1;width:100%;height:.125rem}@media print{.divider:before,.divider:after{border:.5px solid}}.divider:not(:empty){gap:1rem}.filter{flex-wrap:wrap;display:flex}.filter input[type=radio]{width:auto}.filter input{opacity:1;transition:margin .1s,opacity .3s,padding .3s,border-width .1s;overflow:hidden;scale:1}.filter input:not(:last-child){margin-inline-end:.25rem}.filter input.filter-reset{aspect-ratio:1}.filter input.filter-reset:after{--tw-content:"×";content:var(--tw-content)}.filter:not(:has(input:checked:not(.filter-reset))) .filter-reset,.filter:not(:has(input:checked:not(.filter-reset))) input[type=reset],.filter:has(input:checked:not(.filter-reset)) input:not(:checked,.filter-reset,input[type=reset]){opacity:0;border-width:0;width:0;margin-inline:0;padding-inline:0;scale:0}.breadcrumbs{max-width:100%;padding-block:.5rem;overflow-x:auto}.breadcrumbs>menu,.breadcrumbs>ul,.breadcrumbs>ol{white-space:nowrap;align-items:center;min-height:min-content;display:flex}:is(.breadcrumbs>menu,.breadcrumbs>ul,.breadcrumbs>ol)>li{align-items:center;display:flex}:is(.breadcrumbs>menu,.breadcrumbs>ul,.breadcrumbs>ol)>li>*{cursor:pointer;align-items:center;gap:.5rem;display:flex}@media(hover:hover){:is(.breadcrumbs>menu,.breadcrumbs>ul,.breadcrumbs>ol)>li>:hover{text-decoration-line:underline}}:is(.breadcrumbs>menu,.breadcrumbs>ul,.breadcrumbs>ol)>li>:focus{--tw-outline-style:none;outline-style:none}@media(forced-colors:active){:is(.breadcrumbs>menu,.breadcrumbs>ul,.breadcrumbs>ol)>li>:focus{outline-offset:2px;outline:2px solid #0000}}:is(.breadcrumbs>menu,.breadcrumbs>ul,.breadcrumbs>ol)>li>:focus-visible{outline-offset:2px;outline:2px solid}:is(.breadcrumbs>menu,.breadcrumbs>ul,.breadcrumbs>ol)>li+:before{content:"";opacity:.4;background-color:#0000;border-top:1px solid;border-right:1px solid;width:.375rem;height:.375rem;margin-inline:.5rem .75rem;display:block;rotate:45deg}[dir=rtl] :is(:is(.breadcrumbs>menu,.breadcrumbs>ul,.breadcrumbs>ol)>li)+:before{rotate:-135deg}.label{white-space:nowrap;color:currentColor;align-items:center;gap:.375rem;display:inline-flex}@supports (color:color-mix(in lab,red,red)){.label{color:color-mix(in oklab,currentcolor 60%,transparent)}}.label:has(input){cursor:pointer}.label:is(.input>*,.select>*){white-space:nowrap;height:calc(100% - .5rem);font-size:inherit;align-items:center;padding-inline:.75rem;display:flex}.label:is(.input>*,.select>*):first-child{border-inline-end:var(--border) solid currentColor;margin-inline:-.75rem .75rem}@supports (color:color-mix(in lab,red,red)){.label:is(.input>*,.select>*):first-child{border-inline-end:var(--border) solid color-mix(in oklab,currentColor 10%,#0000)}}.label:is(.input>*,.select>*):last-child{border-inline-start:var(--border) solid currentColor;margin-inline:.75rem -.75rem}@supports (color:color-mix(in lab,red,red)){.label:is(.input>*,.select>*):last-child{border-inline-start:var(--border) solid color-mix(in oklab,currentColor 10%,#0000)}}.label\\!{white-space:nowrap!important;color:currentColor!important;align-items:center!important;gap:.375rem!important;display:inline-flex!important}@supports (color:color-mix(in lab,red,red)){.label\\!{color:color-mix(in oklab,currentcolor 60%,transparent)!important}}.label\\!:has(input){cursor:pointer!important}.label\\!:is(.input>*,.select>*){white-space:nowrap!important;height:calc(100% - .5rem)!important;font-size:inherit!important;align-items:center!important;padding-inline:.75rem!important;display:flex!important}.label\\!:is(.input>*,.select>*):first-child{border-inline-end:var(--border) solid currentColor!important;margin-inline:-.75rem .75rem!important}@supports (color:color-mix(in lab,red,red)){.label\\!:is(.input>*,.select>*):first-child{border-inline-end:var(--border) solid color-mix(in oklab,currentColor 10%,#0000)!important}}.label\\!:is(.input>*,.select>*):last-child{border-inline-start:var(--border) solid currentColor!important;margin-inline:.75rem -.75rem!important}@supports (color:color-mix(in lab,red,red)){.label\\!:is(.input>*,.select>*):last-child{border-inline-start:var(--border) solid color-mix(in oklab,currentColor 10%,#0000)!important}}.fieldset-legend{color:var(--color-base-content);justify-content:space-between;align-items:center;gap:.5rem;margin-bottom:-.25rem;padding-block:.5rem;font-weight:600;display:flex}.status{aspect-ratio:1;border-radius:var(--radius-selector);background-color:var(--color-base-content);width:.5rem;height:.5rem;display:inline-block}@supports (color:color-mix(in lab,red,red)){.status{background-color:color-mix(in oklab,var(--color-base-content) 20%,transparent)}}.status{vertical-align:middle;color:#0000004d;background-position:50%;background-repeat:no-repeat}@supports (color:color-mix(in lab,red,red)){.status{color:color-mix(in oklab,var(--color-black) 30%,transparent)}}.status{background-image:radial-gradient(circle at 35% 30%,oklch(1 0 0 / calc(var(--depth) * .5)),#0000);box-shadow:0 2px 3px -1px}@supports (color:color-mix(in lab,red,red)){.status{box-shadow:0 2px 3px -1px color-mix(in oklab,currentColor calc(var(--depth) * 100%),#0000)}}.badge{border-radius:var(--radius-selector);vertical-align:middle;color:var(--badge-fg);border:var(--border) solid var(--badge-color,var(--color-base-200));background-size:auto,calc(var(--noise) * 100%);background-image:none,var(--fx-noise);background-color:var(--badge-bg);--badge-bg:var(--badge-color,var(--color-base-100));--badge-fg:var(--color-base-content);--size:calc(var(--size-selector,.25rem) * 6);width:fit-content;height:var(--size);padding-inline:calc(var(--size) / 2 - var(--border));justify-content:center;align-items:center;gap:.5rem;font-size:.875rem;display:inline-flex}.kbd{border-radius:var(--radius-field);background-color:var(--color-base-200);vertical-align:middle;border:var(--border) solid var(--color-base-content);justify-content:center;align-items:center;padding-inline:.5em;display:inline-flex}@supports (color:color-mix(in lab,red,red)){.kbd{border:var(--border) solid color-mix(in srgb,var(--color-base-content) 20%,#0000)}}.kbd{border-bottom:calc(var(--border) + 1px) solid var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.kbd{border-bottom:calc(var(--border) + 1px) solid color-mix(in srgb,var(--color-base-content) 20%,#0000)}}.kbd{--size:calc(var(--size-selector,.25rem) * 6);height:var(--size);min-width:var(--size);font-size:.875rem}.tabs{--tabs-height:auto;--tabs-direction:row;--tab-height:calc(var(--size-field,.25rem) * 10);height:var(--tabs-height);flex-wrap:wrap;flex-direction:var(--tabs-direction);display:flex}.footer{grid-auto-flow:row;place-items:start;gap:2.5rem 1rem;width:100%;font-size:.875rem;line-height:1.25rem;display:grid}.footer>*{place-items:start;gap:.5rem;display:grid}.footer.footer-center{text-align:center;grid-auto-flow:column dense;place-items:center}.footer.footer-center>*{place-items:center}.stat{grid-template-columns:repeat(1,1fr);column-gap:1rem;width:100%;padding-block:1rem;padding-inline:1.5rem;display:inline-grid}.stat:not(:last-child){border-inline-end:var(--border) dashed currentColor}@supports (color:color-mix(in lab,red,red)){.stat:not(:last-child){border-inline-end:var(--border) dashed color-mix(in oklab,currentColor 10%,#0000)}}.stat:not(:last-child){border-block-end:none}.card-body{padding:var(--card-p,1.5rem);font-size:var(--card-fs,.875rem);flex-direction:column;flex:auto;gap:.5rem;display:flex}.card-body :where(p){flex-grow:1}.fieldset-label{color:var(--color-base-content);align-items:center;gap:.375rem;display:flex}@supports (color:color-mix(in lab,red,red)){.fieldset-label{color:color-mix(in oklab,var(--color-base-content) 60%,transparent)}}.fieldset-label:has(input){cursor:pointer}.alert{--alert-border-color:var(--color-base-200);border-radius:var(--radius-box);color:var(--color-base-content);background-color:var(--alert-color,var(--color-base-200));text-align:start;background-size:auto,calc(var(--noise) * 100%);background-image:none,var(--fx-noise);box-shadow:0 3px 0 -2px oklch(100% 0 0 / calc(var(--depth) * .08)) inset,0 1px #000,0 4px 3px -2px oklch(0% 0 0 / calc(var(--depth) * .08));border-style:solid;grid-template-columns:auto;grid-auto-flow:column;justify-content:start;place-items:center start;gap:1rem;padding-block:.75rem;padding-inline:1rem;font-size:.875rem;line-height:1.25rem;display:grid}@supports (color:color-mix(in lab,red,red)){.alert{box-shadow:0 3px 0 -2px oklch(100% 0 0 / calc(var(--depth) * .08)) inset,0 1px color-mix(in oklab,color-mix(in oklab,#000 20%,var(--alert-color,var(--color-base-200))) calc(var(--depth) * 20%),#0000),0 4px 3px -2px oklch(0% 0 0 / calc(var(--depth) * .08))}}.alert:has(:nth-child(2)){grid-template-columns:auto minmax(auto,1fr)}.fieldset{grid-template-columns:1fr;grid-auto-rows:max-content;gap:.375rem;padding-block:.25rem;font-size:.75rem;display:grid}.chat{--mask-chat:url("data:image/svg+xml,%3csvg width='13' height='13' xmlns='http://www.w3.org/2000/svg'%3e%3cpath fill='black' d='M0 11.5004C0 13.0004 2 13.0004 2 13.0004H12H13V0.00036329L12.5 0C12.5 0 11.977 2.09572 11.8581 2.50033C11.6075 3.35237 10.9149 4.22374 9 5.50036C6 7.50036 0 10.0004 0 11.5004Z'/%3e%3c/svg%3e");grid-auto-rows:min-content;column-gap:.75rem;padding-block:.25rem;display:grid}.card-title{font-size:var(--cardtitle-fs,1.125rem);align-items:center;gap:.5rem;font-weight:600;display:flex}.mask{vertical-align:middle;display:inline-block;-webkit-mask-position:50%;mask-position:50%;-webkit-mask-size:contain;mask-size:contain;-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat}.skeleton{border-radius:var(--radius-box);background-color:var(--color-base-300)}@media(prefers-reduced-motion:reduce){.skeleton{transition-duration:15s}}.skeleton{will-change:background-position;background-image:linear-gradient(105deg,#0000 0% 40%,var(--color-base-100) 50%,#0000 60% 100%);background-position-x:-50%;background-size:200%}@media(prefers-reduced-motion:no-preference){.skeleton{animation:1.8s ease-in-out infinite skeleton}}.link{cursor:pointer;text-decoration-line:underline}.link:focus{--tw-outline-style:none;outline-style:none}@media(forced-colors:active){.link:focus{outline-offset:2px;outline:2px solid #0000}}.link:focus-visible{outline-offset:2px;outline:2px solid}.link\\!{cursor:pointer!important;text-decoration-line:underline!important}.link\\!:focus{--tw-outline-style:none!important;outline-style:none!important}@media(forced-colors:active){.link\\!:focus{outline-offset:2px!important;outline:2px solid #0000!important}}.link\\!:focus-visible{outline-offset:2px!important;outline:2px solid!important}.btn-error{--btn-color:var(--color-error);--btn-fg:var(--color-error-content)}.btn-neutral{--btn-color:var(--color-neutral);--btn-fg:var(--color-neutral-content)}.btn-primary{--btn-color:var(--color-primary);--btn-fg:var(--color-primary-content)}}.\\@container{container-type:inline-size}@layer daisyui.l1.l2{.modal.modal-open,.modal[open],.modal:target,.modal-toggle:checked+.modal{pointer-events:auto;visibility:visible;opacity:1;transition:visibility 0s allow-discrete,background-color .3s ease-out,opacity .1s ease-out;background-color:#0006}:is(.modal.modal-open,.modal[open],.modal:target,.modal-toggle:checked+.modal) .modal-box{opacity:1;translate:0;scale:1}:root:has(:is(.modal.modal-open,.modal[open],.modal:target,.modal-toggle:checked+.modal)){--page-has-backdrop:1;--page-overflow:hidden;--page-scroll-bg:var(--page-scroll-bg-on);--page-scroll-gutter:stable;--page-scroll-transition:var(--page-scroll-transition-on);animation:forwards set-page-has-scroll;animation-timeline:scroll()}@starting-style{.modal.modal-open,.modal[open],.modal:target,.modal-toggle:checked+.modal{opacity:0}}.tooltip>.tooltip-content,.tooltip[data-tip]:before{transform:translate(-50%) translateY(var(--tt-pos,.25rem));inset:auto auto var(--tt-off) 50%}.tooltip:after{transform:translate(-50%) translateY(var(--tt-pos,.25rem));inset:auto auto var(--tt-tail) 50%}.btn:disabled:not(.btn-link,.btn-ghost){background-color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.btn:disabled:not(.btn-link,.btn-ghost){background-color:color-mix(in oklab,var(--color-base-content) 10%,transparent)}}.btn:disabled:not(.btn-link,.btn-ghost){box-shadow:none}.btn:disabled{pointer-events:none;--btn-border:#0000;--btn-noise:none;--btn-fg:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.btn:disabled{--btn-fg:color-mix(in oklch, var(--color-base-content) 20%, #0000)}}.btn[disabled]:not(.btn-link,.btn-ghost){background-color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.btn[disabled]:not(.btn-link,.btn-ghost){background-color:color-mix(in oklab,var(--color-base-content) 10%,transparent)}}.btn[disabled]:not(.btn-link,.btn-ghost){box-shadow:none}.btn[disabled]{pointer-events:none;--btn-border:#0000;--btn-noise:none;--btn-fg:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.btn[disabled]{--btn-fg:color-mix(in oklch, var(--color-base-content) 20%, #0000)}}.btn-disabled:not(.btn-link,.btn-ghost){background-color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.btn-disabled:not(.btn-link,.btn-ghost){background-color:color-mix(in oklab,var(--color-base-content) 10%,transparent)}}.btn-disabled:not(.btn-link,.btn-ghost){box-shadow:none}.btn-disabled{pointer-events:none;--btn-border:#0000;--btn-noise:none;--btn-fg:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.btn-disabled{--btn-fg:color-mix(in oklch, var(--color-base-content) 20%, #0000)}}@media(prefers-reduced-motion:no-preference){.collapse[open].collapse-arrow>.collapse-title:after,.collapse.collapse-open.collapse-arrow>.collapse-title:after{transform:translateY(-50%)rotate(225deg)}}.collapse.collapse-open.collapse-plus>.collapse-title:after{--tw-content:"−";content:var(--tw-content)}:is(.collapse[tabindex].collapse-arrow:focus:not(.collapse-close),.collapse.collapse-arrow[tabindex]:focus-within:not(.collapse-close))>.collapse-title:after,.collapse.collapse-arrow:not(.collapse-close)>input:is([type=checkbox],[type=radio]):checked~.collapse-title:after{transform:translateY(-50%)rotate(225deg)}.collapse[open].collapse-plus>.collapse-title:after,.collapse[tabindex].collapse-plus:focus:not(.collapse-close)>.collapse-title:after,.collapse.collapse-plus:not(.collapse-close)>input:is([type=checkbox],[type=radio]):checked~.collapse-title:after{--tw-content:"−";content:var(--tw-content)}.list .list-row:has(.list-col-grow:first-child){--list-grid-cols:1fr}.list .list-row:has(.list-col-grow:nth-child(2)){--list-grid-cols:minmax(0, auto) 1fr}.list .list-row:has(.list-col-grow:nth-child(3)){--list-grid-cols:minmax(0, auto) minmax(0, auto) 1fr}.list .list-row:has(.list-col-grow:nth-child(4)){--list-grid-cols:minmax(0, auto) minmax(0, auto) minmax(0, auto) 1fr}.list .list-row:has(.list-col-grow:nth-child(5)){--list-grid-cols:minmax(0, auto) minmax(0, auto) minmax(0, auto) minmax(0, auto) 1fr}.list .list-row:has(.list-col-grow:nth-child(6)){--list-grid-cols:minmax(0, auto) minmax(0, auto) minmax(0, auto) minmax(0, auto) minmax(0, auto) 1fr}.list .list-row>*{grid-row-start:1}.list\\! .list-row:has(.list-col-grow:first-child){--list-grid-cols:1fr!important}.list\\! .list-row:has(.list-col-grow:nth-child(2)){--list-grid-cols:minmax(0, auto) 1fr!important}.list\\! .list-row:has(.list-col-grow:nth-child(3)){--list-grid-cols:minmax(0, auto) minmax(0, auto) 1fr!important}.list\\! .list-row:has(.list-col-grow:nth-child(4)){--list-grid-cols:minmax(0, auto) minmax(0, auto) minmax(0, auto) 1fr!important}.list\\! .list-row:has(.list-col-grow:nth-child(5)){--list-grid-cols:minmax(0, auto) minmax(0, auto) minmax(0, auto) minmax(0, auto) 1fr!important}.list\\! .list-row:has(.list-col-grow:nth-child(6)){--list-grid-cols:minmax(0, auto) minmax(0, auto) minmax(0, auto) minmax(0, auto) minmax(0, auto) 1fr!important}.list\\! .list-row>*{grid-row-start:1!important}.steps .step-neutral+.step-neutral:before,.steps .step-neutral:after,.steps .step-neutral>.step-icon{--step-bg:var(--color-neutral);--step-fg:var(--color-neutral-content)}.steps .step-primary+.step-primary:before,.steps .step-primary:after,.steps .step-primary>.step-icon{--step-bg:var(--color-primary);--step-fg:var(--color-primary-content)}.steps .step-secondary+.step-secondary:before,.steps .step-secondary:after,.steps .step-secondary>.step-icon{--step-bg:var(--color-secondary);--step-fg:var(--color-secondary-content)}.steps .step-accent+.step-accent:before,.steps .step-accent:after,.steps .step-accent>.step-icon{--step-bg:var(--color-accent);--step-fg:var(--color-accent-content)}.steps .step-info+.step-info:before,.steps .step-info:after,.steps .step-info>.step-icon{--step-bg:var(--color-info);--step-fg:var(--color-info-content)}.steps .step-success+.step-success:before,.steps .step-success:after,.steps .step-success>.step-icon{--step-bg:var(--color-success);--step-fg:var(--color-success-content)}.steps .step-warning+.step-warning:before,.steps .step-warning:after,.steps .step-warning>.step-icon{--step-bg:var(--color-warning);--step-fg:var(--color-warning-content)}.steps .step-error+.step-error:before,.steps .step-error:after,.steps .step-error>.step-icon{--step-bg:var(--color-error);--step-fg:var(--color-error-content)}.steps\\! .step-neutral+.step-neutral:before,.steps\\! .step-neutral:after,.steps\\! .step-neutral>.step-icon{--step-bg:var(--color-neutral)!important;--step-fg:var(--color-neutral-content)!important}.steps\\! .step-primary+.step-primary:before,.steps\\! .step-primary:after,.steps\\! .step-primary>.step-icon{--step-bg:var(--color-primary)!important;--step-fg:var(--color-primary-content)!important}.steps\\! .step-secondary+.step-secondary:before,.steps\\! .step-secondary:after,.steps\\! .step-secondary>.step-icon{--step-bg:var(--color-secondary)!important;--step-fg:var(--color-secondary-content)!important}.steps\\! .step-accent+.step-accent:before,.steps\\! .step-accent:after,.steps\\! .step-accent>.step-icon{--step-bg:var(--color-accent)!important;--step-fg:var(--color-accent-content)!important}.steps\\! .step-info+.step-info:before,.steps\\! .step-info:after,.steps\\! .step-info>.step-icon{--step-bg:var(--color-info)!important;--step-fg:var(--color-info-content)!important}.steps\\! .step-success+.step-success:before,.steps\\! .step-success:after,.steps\\! .step-success>.step-icon{--step-bg:var(--color-success)!important;--step-fg:var(--color-success-content)!important}.steps\\! .step-warning+.step-warning:before,.steps\\! .step-warning:after,.steps\\! .step-warning>.step-icon{--step-bg:var(--color-warning)!important;--step-fg:var(--color-warning-content)!important}.steps\\! .step-error+.step-error:before,.steps\\! .step-error:after,.steps\\! .step-error>.step-icon{--step-bg:var(--color-error)!important;--step-fg:var(--color-error-content)!important}.checkbox:disabled,.radio:disabled{cursor:not-allowed;opacity:.2}.rating.rating-xs :where(:not(.rating-hidden)){width:1rem;height:1rem}.rating.rating-sm :where(:not(.rating-hidden)){width:1.25rem;height:1.25rem}.rating.rating-md :where(:not(.rating-hidden)){width:1.5rem;height:1.5rem}.rating.rating-lg :where(:not(.rating-hidden)){width:1.75rem;height:1.75rem}.rating.rating-xl :where(:not(.rating-hidden)){width:2rem;height:2rem}.rating\\!.rating-xs :where(:not(.rating-hidden)){width:1rem!important;height:1rem!important}.rating\\!.rating-sm :where(:not(.rating-hidden)){width:1.25rem!important;height:1.25rem!important}.rating\\!.rating-md :where(:not(.rating-hidden)){width:1.5rem!important;height:1.5rem!important}.rating\\!.rating-lg :where(:not(.rating-hidden)){width:1.75rem!important;height:1.75rem!important}.rating\\!.rating-xl :where(:not(.rating-hidden)){width:2rem!important;height:2rem!important}:where(.navbar){position:relative}.toast-center{--toast-x:-50%;inset-inline:50%}.toast-start{--toast-x:0;inset-inline:1rem auto}.toast-top{--toast-y:0;top:1rem;bottom:auto}.btn-active{--btn-bg:var(--btn-color,var(--color-base-200))}@supports (color:color-mix(in lab,red,red)){.btn-active{--btn-bg:color-mix(in oklab, var(--btn-color,var(--color-base-200)), #000 7%)}}.btn-active{--btn-shadow:0 0 0 0 oklch(0% 0 0/0), 0 0 0 0 oklch(0% 0 0/0);isolation:isolate}:is(.stack,.stack.stack-bottom)>*{grid-area:3/3/6/4}:is(.stack,.stack.stack-bottom)>:nth-child(2){grid-area:2/2/5/5}:is(.stack,.stack.stack-bottom)>:first-child{grid-area:1/1/4/6}.stack.stack-top>*{grid-area:1/3/4/4}.stack.stack-top>:nth-child(2){grid-area:2/2/5/5}.stack.stack-top>:first-child{grid-area:3/1/6/6}.stack.stack-start>*{grid-area:3/1/4/4}.stack.stack-start>:nth-child(2){grid-area:2/2/5/5}.stack.stack-start>:first-child{grid-area:1/3/6/6}.stack.stack-end>*{grid-area:3/3/4/6}.stack.stack-end>:nth-child(2){grid-area:2/2/5/5}.stack.stack-end>:first-child{grid-area:1/1/6/4}.input-md{--size:calc(var(--size-field,.25rem) * 10);font-size:max(var(--font-size,.875rem),.875rem)}.input-md[type=number]::-webkit-inner-spin-button{margin-block:-.75rem;margin-inline-end:-.75rem}.btn-circle{width:var(--size);height:var(--size);border-radius:3.40282e38px;padding-inline:0}.btn-square{width:var(--size);height:var(--size);padding-inline:0}.loading-sm{width:calc(var(--size-selector,.25rem) * 5)}.badge-ghost{border-color:var(--color-base-200);background-color:var(--color-base-200);color:var(--color-base-content);background-image:none}.loading-spinner{-webkit-mask-image:url("data:image/svg+xml,%3Csvg width='24' height='24' stroke='black' viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'%3E%3Cg transform-origin='center'%3E%3Ccircle cx='12' cy='12' r='9.5' fill='none' stroke-width='3' stroke-linecap='round'%3E%3CanimateTransform attributeName='transform' type='rotate' from='0 12 12' to='360 12 12' dur='2s' repeatCount='indefinite'/%3E%3Canimate attributeName='stroke-dasharray' values='0,150;42,150;42,150' keyTimes='0;0.475;1' dur='1.5s' repeatCount='indefinite'/%3E%3Canimate attributeName='stroke-dashoffset' values='0;-16;-59' keyTimes='0;0.475;1' dur='1.5s' repeatCount='indefinite'/%3E%3C/circle%3E%3C/g%3E%3C/svg%3E");mask-image:url("data:image/svg+xml,%3Csvg width='24' height='24' stroke='black' viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'%3E%3Cg transform-origin='center'%3E%3Ccircle cx='12' cy='12' r='9.5' fill='none' stroke-width='3' stroke-linecap='round'%3E%3CanimateTransform attributeName='transform' type='rotate' from='0 12 12' to='360 12 12' dur='2s' repeatCount='indefinite'/%3E%3Canimate attributeName='stroke-dasharray' values='0,150;42,150;42,150' keyTimes='0;0.475;1' dur='1.5s' repeatCount='indefinite'/%3E%3Canimate attributeName='stroke-dashoffset' values='0;-16;-59' keyTimes='0;0.475;1' dur='1.5s' repeatCount='indefinite'/%3E%3C/circle%3E%3C/g%3E%3C/svg%3E")}.checkbox-lg{--size:calc(var(--size-selector,.25rem) * 7);padding:.3125rem}.checkbox-sm{--size:calc(var(--size-selector,.25rem) * 5);padding:.1875rem}.badge-lg{--size:calc(var(--size-selector,.25rem) * 7);font-size:1rem}.badge-sm{--size:calc(var(--size-selector,.25rem) * 5);font-size:.75rem}.badge-xs{--size:calc(var(--size-selector,.25rem) * 4);font-size:.625rem}.alert-error{color:var(--color-error-content);--alert-border-color:var(--color-error);--alert-color:var(--color-error)}.alert-info{color:var(--color-info-content);--alert-border-color:var(--color-info);--alert-color:var(--color-info)}.alert-success{color:var(--color-success-content);--alert-border-color:var(--color-success);--alert-color:var(--color-success)}.alert-warning{color:var(--color-warning-content);--alert-border-color:var(--color-warning);--alert-color:var(--color-warning)}.link-error{color:var(--color-error)}@media(hover:hover){.link-error:hover{color:var(--color-error)}@supports (color:color-mix(in lab,red,red)){.link-error:hover{color:color-mix(in oklab,var(--color-error) 80%,#000)}}}.link-neutral{color:var(--color-neutral)}@media(hover:hover){.link-neutral:hover{color:var(--color-neutral)}@supports (color:color-mix(in lab,red,red)){.link-neutral:hover{color:color-mix(in oklab,var(--color-neutral) 80%,#000)}}}.link-primary{color:var(--color-primary)}@media(hover:hover){.link-primary:hover{color:var(--color-primary)}@supports (color:color-mix(in lab,red,red)){.link-primary:hover{color:color-mix(in oklab,var(--color-primary) 80%,#000)}}}.btn-lg{--fontsize:1.125rem;--btn-p:1.25rem;--size:calc(var(--size-field,.25rem) * 12)}.btn-sm{--fontsize:.75rem;--btn-p:.75rem;--size:calc(var(--size-field,.25rem) * 8)}.badge-success{--badge-color:var(--color-success);--badge-fg:var(--color-success-content)}.input-error,.input-error:focus,.input-error:focus-within{--input-color:var(--color-error)}}.pointer-events-none{pointer-events:none}.countdown.countdown{line-height:1em}.collapse:not(td,tr,colgroup){visibility:revert-layer}.validator:user-invalid~.validator-hint{display:revert-layer}.validator:has(:user-invalid)~.validator-hint{display:revert-layer}:is(.validator[aria-invalid]:not([aria-invalid=false]),.validator:has([aria-invalid]:not([aria-invalid=false])))~.validator-hint{display:revert-layer}.collapse{visibility:collapse}.invisible{visibility:hidden}.visible{visibility:visible}.sr-only{clip-path:inset(50%);white-space:nowrap;border-width:0;width:1px;height:1px;margin:-1px;padding:0;position:absolute;overflow:hidden}.\\!absolute{position:absolute!important}.\\!static{position:static!important}.absolute{position:absolute}.fixed{position:fixed}.relative{position:relative}.static{position:static}.sticky{position:sticky}.join{--join-ss:0;--join-se:0;--join-es:0;--join-ee:0;align-items:stretch;display:inline-flex}.join :where(.join-item){border-start-start-radius:var(--join-ss,0);border-start-end-radius:var(--join-se,0);border-end-end-radius:var(--join-ee,0);border-end-start-radius:var(--join-es,0)}.join :where(.join-item) *{--join-ss:var(--radius-field);--join-se:var(--radius-field);--join-es:var(--radius-field);--join-ee:var(--radius-field)}.join>.join-item:where(:first-child),.join :first-child:not(:last-child) :where(.join-item){--join-ss:var(--radius-field);--join-se:0;--join-es:var(--radius-field);--join-ee:0}.join>.join-item:where(:last-child),.join :last-child:not(:first-child) :where(.join-item){--join-ss:0;--join-se:var(--radius-field);--join-es:0;--join-ee:var(--radius-field)}.join>.join-item:where(:only-child),.join :only-child :where(.join-item){--join-ss:var(--radius-field);--join-se:var(--radius-field);--join-es:var(--radius-field);--join-ee:var(--radius-field)}.join>:where(:focus,:has(:focus)){z-index:1}@media(hover:hover){.join>:where(.btn:hover,:has(.btn:hover)){isolation:isolate}}.isolate{isolation:isolate}.\\!container{width:100%!important}@media(min-width:40rem){.\\!container{max-width:40rem!important}}@media(min-width:48rem){.\\!container{max-width:48rem!important}}@media(min-width:64rem){.\\!container{max-width:64rem!important}}@media(min-width:80rem){.\\!container{max-width:80rem!important}}@media(min-width:96rem){.\\!container{max-width:96rem!important}}.container{width:100%}@media(min-width:40rem){.container{max-width:40rem}}@media(min-width:48rem){.container{max-width:48rem}}@media(min-width:64rem){.container{max-width:64rem}}@media(min-width:80rem){.container{max-width:80rem}}@media(min-width:96rem){.container{max-width:96rem}}.m-0{margin:calc(var(--spacing) * 0)}.mx-auto{margin-inline:auto}.mt-940{margin-top:calc(var(--spacing) * 940)}.mb-1{margin-bottom:calc(var(--spacing) * 1)}.ml-1{margin-left:calc(var(--spacing) * 1)}.ml-2{margin-left:calc(var(--spacing) * 2)}.ml-auto{margin-left:auto}.kbd{box-shadow:none}.alert{border-width:var(--border);border-color:var(--alert-border-color,var(--color-base-200))}:root .prose{--tw-prose-body:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){:root .prose{--tw-prose-body:color-mix(in oklab, var(--color-base-content) 80%, #0000)}}:root .prose{--tw-prose-headings:var(--color-base-content);--tw-prose-lead:var(--color-base-content);--tw-prose-links:var(--color-base-content);--tw-prose-bold:var(--color-base-content);--tw-prose-counters:var(--color-base-content);--tw-prose-bullets:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){:root .prose{--tw-prose-bullets:color-mix(in oklab, var(--color-base-content) 50%, #0000)}}:root .prose{--tw-prose-hr:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){:root .prose{--tw-prose-hr:color-mix(in oklab, var(--color-base-content) 20%, #0000)}}:root .prose{--tw-prose-quotes:var(--color-base-content);--tw-prose-quote-borders:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){:root .prose{--tw-prose-quote-borders:color-mix(in oklab, var(--color-base-content) 20%, #0000)}}:root .prose{--tw-prose-captions:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){:root .prose{--tw-prose-captions:color-mix(in oklab, var(--color-base-content) 50%, #0000)}}:root .prose{--tw-prose-code:var(--color-base-content);--tw-prose-pre-code:var(--color-neutral-content);--tw-prose-pre-bg:var(--color-neutral);--tw-prose-th-borders:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){:root .prose{--tw-prose-th-borders:color-mix(in oklab, var(--color-base-content) 50%, #0000)}}:root .prose{--tw-prose-td-borders:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){:root .prose{--tw-prose-td-borders:color-mix(in oklab, var(--color-base-content) 20%, #0000)}}:root .prose{--tw-prose-kbd:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){:root .prose{--tw-prose-kbd:color-mix(in oklab, var(--color-base-content) 80%, #0000)}}:root .prose :where(code):not(pre>code){background-color:var(--color-base-200);border-radius:var(--radius-selector);border:var(--border) solid var(--color-base-300);font-weight:inherit;padding-block:.2em;padding-inline:.5em}:root .prose :where(code):not(pre>code):before,:root .prose :where(code):not(pre>code):after{display:none}.block{display:block}.contents{display:contents}.flex{display:flex}.grid{display:grid}.hidden{display:none}.inline{display:inline}.table{display:table}.table-cell{display:table-cell}.table-footer-group{display:table-footer-group}.table-header-group{display:table-header-group}.table-row{display:table-row}.table-row-group{display:table-row-group}.size-0{width:calc(var(--spacing) * 0);height:calc(var(--spacing) * 0)}.h-5{height:calc(var(--spacing) * 5)}.max-h-60{max-height:calc(var(--spacing) * 60)}.w-5{width:calc(var(--spacing) * 5)}.w-48{width:calc(var(--spacing) * 48)}.w-full{width:100%}.min-w-0{min-width:calc(var(--spacing) * 0)}.flex-1{flex:1}.flex-shrink,.shrink{flex-shrink:1}.shrink-0{flex-shrink:0}.flex-grow,.grow{flex-grow:1}.scale-15878{--tw-scale-x:15878%;--tw-scale-y:15878%;--tw-scale-z:15878%;scale:var(--tw-scale-x) var(--tw-scale-y)}.rotate-180{rotate:180deg}.transform{transform:var(--tw-rotate-x,) var(--tw-rotate-y,) var(--tw-rotate-z,) var(--tw-skew-x,) var(--tw-skew-y,)}.cursor-not-allowed{cursor:not-allowed}.cursor-pointer{cursor:pointer}.resize{resize:both}.flex-col{flex-direction:column}.flex-wrap{flex-wrap:wrap}.items-center{align-items:center}.items-start{align-items:flex-start}.items-stretch{align-items:stretch}.justify-between{justify-content:space-between}.justify-end{justify-content:flex-end}.justify-start{justify-content:flex-start}.gap-1{gap:calc(var(--spacing) * 1)}.gap-2{gap:calc(var(--spacing) * 2)}.gap-3{gap:calc(var(--spacing) * 3)}.gap-4{gap:calc(var(--spacing) * 4)}.self-center{align-self:center}.truncate{text-overflow:ellipsis;white-space:nowrap;overflow:hidden}.overflow-x-auto{overflow-x:auto}.overflow-y-auto{overflow-y:auto}.rounded{border-radius:.25rem}.rounded-box{border-radius:var(--radius-box)}.border{border-style:var(--tw-border-style);border-width:1px}.border-b{border-bottom-style:var(--tw-border-style);border-bottom-width:1px}.border-l-2{border-left-style:var(--tw-border-style);border-left-width:2px}.border-base-300{border-color:var(--color-base-300)}.border-primary{border-color:var(--color-primary)}.glass{-webkit-backdrop-filter:blur(var(--glass-blur,40px));backdrop-filter:blur(var(--glass-blur,40px));background-color:#0000;background-image:linear-gradient(135deg,oklch(100% 0 0 / var(--glass-opacity,30%)),#0000),linear-gradient(var(--glass-reflect-degree,100deg),oklch(100% 0 0 / var(--glass-reflect-opacity,5%)) 25%,oklch(0% 0 0/0) 25%);box-shadow:0 0 0 1px oklch(100% 0 0 / var(--glass-border-opacity,20%)) inset,0 0 0 2px #0000000d;text-shadow:0 1px oklch(0% 0 0 / var(--glass-text-shadow-opacity,5%));border:none}.bg-base-100{background-color:var(--color-base-100)}.bg-base-200{background-color:var(--color-base-200)}.bg-primary,.bg-primary\\/10{background-color:var(--color-primary)}@supports (color:color-mix(in lab,red,red)){.bg-primary\\/10{background-color:color-mix(in oklab,var(--color-primary) 10%,transparent)}}.p-4{padding:calc(var(--spacing) * 4)}.px-3{padding-inline:calc(var(--spacing) * 3)}.px-4{padding-inline:calc(var(--spacing) * 4)}.py-2{padding-block:calc(var(--spacing) * 2)}.py-3{padding-block:calc(var(--spacing) * 3)}.py-4{padding-block:calc(var(--spacing) * 4)}.py-8{padding-block:calc(var(--spacing) * 8)}.pt-2{padding-top:calc(var(--spacing) * 2)}.pb-1{padding-bottom:calc(var(--spacing) * 1)}.pl-1{padding-left:calc(var(--spacing) * 1)}.pl-58661{padding-left:calc(var(--spacing) * 58661)}.text-center{text-align:center}.text-2xl{font-size:var(--text-2xl);line-height:var(--tw-leading,var(--text-2xl--line-height))}.text-3xl{font-size:var(--text-3xl);line-height:var(--tw-leading,var(--text-3xl--line-height))}.text-base{font-size:var(--text-base);line-height:var(--tw-leading,var(--text-base--line-height))}.text-lg{font-size:var(--text-lg);line-height:var(--tw-leading,var(--text-lg--line-height))}.text-sm{font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height))}.text-xl{font-size:var(--text-xl);line-height:var(--tw-leading,var(--text-xl--line-height))}.text-xs{font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height))}.leading-77677{--tw-leading:calc(var(--spacing) * 77677);line-height:calc(var(--spacing) * 77677)}.font-bold{--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold)}.font-medium{--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium)}.font-semibold{--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold)}.tracking-wide{--tw-tracking:var(--tracking-wide);letter-spacing:var(--tracking-wide)}.whitespace-nowrap{white-space:nowrap}.text-base-content\\/70{color:var(--color-base-content)}@supports (color:color-mix(in lab,red,red)){.text-base-content\\/70{color:color-mix(in oklab,var(--color-base-content) 70%,transparent)}}.text-error{color:var(--color-error)}.text-neutral{color:var(--color-neutral)}.text-primary{color:var(--color-primary)}.capitalize{text-transform:capitalize}.lowercase{text-transform:lowercase}.uppercase{text-transform:uppercase}.italic{font-style:italic}.ordinal{--tw-ordinal:ordinal;font-variant-numeric:var(--tw-ordinal,) var(--tw-slashed-zero,) var(--tw-numeric-figure,) var(--tw-numeric-spacing,) var(--tw-numeric-fraction,)}.prose :where(a.btn:not(.btn-link)):not(:where([class~=not-prose],[class~=not-prose] *)){text-decoration-line:none}.underline{text-decoration-line:underline}.antialiased{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}.opacity-50{opacity:.5}.opacity-60{opacity:.6}.shadow,.shadow-sm{--tw-shadow:0 1px 3px 0 var(--tw-shadow-color,#0000001a), 0 1px 2px -1px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow)}.ring{--tw-ring-shadow:var(--tw-ring-inset,) 0 0 0 calc(1px + var(--tw-ring-offset-width)) var(--tw-ring-color,currentcolor);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow)}.outline{outline-style:var(--tw-outline-style);outline-width:1px}.outline-18360{outline-style:var(--tw-outline-style);outline-width:18360px}@layer daisyui.l1{.btn-ghost:not(.btn-active,:hover,:active:focus,:focus-visible,input:checked:not(.filter .btn)){--btn-shadow:"";--btn-bg:#0000;--btn-border:#0000;--btn-noise:none}.btn-ghost:not(.btn-active,:hover,:active:focus,:focus-visible,input:checked:not(.filter .btn)):not(:disabled,[disabled],.btn-disabled){--btn-fg:var(--btn-color,currentColor);outline-color:currentColor}@media(hover:none){.btn-ghost:not(.btn-active,:active,:focus-visible,input:checked:not(.filter .btn)):hover{--btn-shadow:"";--btn-bg:#0000;--btn-fg:var(--btn-color,currentColor);--btn-border:#0000;--btn-noise:none;outline-color:currentColor}}}.blur{--tw-blur:blur(8px);filter:var(--tw-blur,) var(--tw-brightness,) var(--tw-contrast,) var(--tw-grayscale,) var(--tw-hue-rotate,) var(--tw-invert,) var(--tw-saturate,) var(--tw-sepia,) var(--tw-drop-shadow,)}.grayscale{--tw-grayscale:grayscale(100%);filter:var(--tw-blur,) var(--tw-brightness,) var(--tw-contrast,) var(--tw-grayscale,) var(--tw-hue-rotate,) var(--tw-invert,) var(--tw-saturate,) var(--tw-sepia,) var(--tw-drop-shadow,)}.invert{--tw-invert:invert(100%);filter:var(--tw-blur,) var(--tw-brightness,) var(--tw-contrast,) var(--tw-grayscale,) var(--tw-hue-rotate,) var(--tw-invert,) var(--tw-saturate,) var(--tw-sepia,) var(--tw-drop-shadow,)}.sepia{--tw-sepia:sepia(100%);filter:var(--tw-blur,) var(--tw-brightness,) var(--tw-contrast,) var(--tw-grayscale,) var(--tw-hue-rotate,) var(--tw-invert,) var(--tw-saturate,) var(--tw-sepia,) var(--tw-drop-shadow,)}.filter{filter:var(--tw-blur,) var(--tw-brightness,) var(--tw-contrast,) var(--tw-grayscale,) var(--tw-hue-rotate,) var(--tw-invert,) var(--tw-saturate,) var(--tw-sepia,) var(--tw-drop-shadow,)}.transition{transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to,opacity,box-shadow,transform,translate,scale,rotate,filter,-webkit-backdrop-filter,backdrop-filter,display,content-visibility,overlay,pointer-events;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration))}.select-all{-webkit-user-select:all;user-select:all}.select-none{-webkit-user-select:none;user-select:none}.\\[a\\:x\\]{a:x}.\\[hw\\:1\\]{hw:1}.\\[mailto\\:marco-oweber\\@gmx\\.de\\]{mailto:marco-oweber@gmx.de}.\\[nix-shell\\:\\~\\]{nix-shell:~}.\\[plughw\\:1\\,0\\]{plughw:1,0}.\\[rightalt\\:G\\]{rightalt:G}.\\[testenv\\:docs\\]{testenv:docs}.\\[tool\\:pytest\\]{tool:pytest}.\\[translation\\:info\\]{translation:info}.\\[tytso\\:19940520\\.0036EDT\\]{tytso:19940500EDT}.\\[vhost\\:www\\.example\\.com\\]{vhost:www.example.com}.block-1{block-size:calc(var(--spacing) * 1)}.block-2{block-size:calc(var(--spacing) * 2)}.block-17209{block-size:calc(var(--spacing) * 17209)}@media(hover:hover){.hover\\:bg-base-200:hover{background-color:var(--color-base-200)}}}:root{--u-tint-weak:12%}html{font-size:18px}.u-dismiss-btn{color:var(--color-base-content);box-shadow:none;border-color:#0000;font-size:1rem}.u-dismiss-btn:hover{box-shadow:none;background-color:currentColor;border-color:#0000}@supports (color:color-mix(in lab,red,red)){.u-dismiss-btn:hover{background-color:color-mix(in srgb,currentColor var(--u-tint-weak),transparent)}}:is(u-page:not(:defined),u-container:not(:defined),u-hstack:not(:defined),u-vstack:not(:defined),u-spacer:not(:defined),u-page-header:not(:defined),u-card:not(:defined),u-form:not(:defined),u-button:not(:defined),u-confirm-action:not(:defined),u-checkbox:not(:defined),u-form-field:not(:defined),u-input:not(:defined),u-combobox-item:not(:defined),u-combobox:not(:defined),u-multiselect-option:not(:defined),u-multiselect:not(:defined),u-list-select-item:not(:defined),u-list-select-group:not(:defined),u-list-select:not(:defined),u-badge:not(:defined),u-table:not(:defined),u-tbody:not(:defined),u-tr:not(:defined),u-th:not(:defined),u-td:not(:defined),u-description-list:not(:defined),u-description-item:not(:defined),u-theme-toggle:not(:defined),u-link:not(:defined),u-emphasize:not(:defined),u-collapsible:not(:defined),u-toast-item:not(:defined),u-toast:not(:defined)){visibility:hidden}@keyframes rating{0%,40%{filter:brightness(1.05)contrast(1.05);scale:1.1}}@keyframes menu{0%{opacity:0}}@keyframes rotator{89.9999%,to{--first-item-position:0 0%}90%,99.9999%{--first-item-position:0 calc(var(--items) * 100%)}to{translate:0 -100%}}@keyframes progress{50%{background-position-x:-115%}}@keyframes radio{0%{padding:5px}50%{padding:3px}}@keyframes dropdown{0%{opacity:0}}@keyframes toast{0%{opacity:0;scale:.9}to{opacity:1;scale:1}}@keyframes skeleton{0%{background-position:150%}to{background-position:-50%}}@property --tw-scale-x{syntax:"*";inherits:false;initial-value:1}@property --tw-scale-y{syntax:"*";inherits:false;initial-value:1}@property --tw-scale-z{syntax:"*";inherits:false;initial-value:1}@property --tw-rotate-x{syntax:"*";inherits:false}@property --tw-rotate-y{syntax:"*";inherits:false}@property --tw-rotate-z{syntax:"*";inherits:false}@property --tw-skew-x{syntax:"*";inherits:false}@property --tw-skew-y{syntax:"*";inherits:false}@property --tw-border-style{syntax:"*";inherits:false;initial-value:solid}@property --tw-leading{syntax:"*";inherits:false}@property --tw-font-weight{syntax:"*";inherits:false}@property --tw-tracking{syntax:"*";inherits:false}@property --tw-ordinal{syntax:"*";inherits:false}@property --tw-slashed-zero{syntax:"*";inherits:false}@property --tw-numeric-figure{syntax:"*";inherits:false}@property --tw-numeric-spacing{syntax:"*";inherits:false}@property --tw-numeric-fraction{syntax:"*";inherits:false}@property --tw-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-shadow-color{syntax:"*";inherits:false}@property --tw-shadow-alpha{syntax:"<percentage>";inherits:false;initial-value:100%}@property --tw-inset-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-inset-shadow-color{syntax:"*";inherits:false}@property --tw-inset-shadow-alpha{syntax:"<percentage>";inherits:false;initial-value:100%}@property --tw-ring-color{syntax:"*";inherits:false}@property --tw-ring-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-inset-ring-color{syntax:"*";inherits:false}@property --tw-inset-ring-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-ring-inset{syntax:"*";inherits:false}@property --tw-ring-offset-width{syntax:"<length>";inherits:false;initial-value:0}@property --tw-ring-offset-color{syntax:"*";inherits:false;initial-value:#fff}@property --tw-ring-offset-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-outline-style{syntax:"*";inherits:false;initial-value:solid}@property --tw-blur{syntax:"*";inherits:false}@property --tw-brightness{syntax:"*";inherits:false}@property --tw-contrast{syntax:"*";inherits:false}@property --tw-grayscale{syntax:"*";inherits:false}@property --tw-hue-rotate{syntax:"*";inherits:false}@property --tw-invert{syntax:"*";inherits:false}@property --tw-opacity{syntax:"*";inherits:false}@property --tw-saturate{syntax:"*";inherits:false}@property --tw-sepia{syntax:"*";inherits:false}@property --tw-drop-shadow{syntax:"*";inherits:false}@property --tw-drop-shadow-color{syntax:"*";inherits:false}@property --tw-drop-shadow-alpha{syntax:"<percentage>";inherits:false;initial-value:100%}@property --tw-drop-shadow-size{syntax:"*";inherits:false}`;
/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const D = globalThis, xe = D.ShadowRoot && (D.ShadyCSS === void 0 || D.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, ye = Symbol(), _e = /* @__PURE__ */ new WeakMap();
let Be = class {
  constructor(e, t, o) {
    if (this._$cssResult$ = !0, o !== ye) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = t;
  }
  get styleSheet() {
    let e = this.o;
    const t = this.t;
    if (xe && e === void 0) {
      const o = t !== void 0 && t.length === 1;
      o && (e = _e.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), o && _e.set(t, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const Qe = (i) => new Be(typeof i == "string" ? i : i + "", void 0, ye), h = (i, ...e) => {
  const t = i.length === 1 ? i[0] : e.reduce((o, r, a) => o + ((s) => {
    if (s._$cssResult$ === !0) return s.cssText;
    if (typeof s == "number") return s;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + s + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + i[a + 1], i[0]);
  return new Be(t, i, ye);
}, Ge = (i, e) => {
  if (xe) i.adoptedStyleSheets = e.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
  else for (const t of e) {
    const o = document.createElement("style"), r = D.litNonce;
    r !== void 0 && o.setAttribute("nonce", r), o.textContent = t.cssText, i.appendChild(o);
  }
}, $e = xe ? (i) => i : (i) => i instanceof CSSStyleSheet ? ((e) => {
  let t = "";
  for (const o of e.cssRules) t += o.cssText;
  return Qe(t);
})(i) : i;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: Je, defineProperty: et, getOwnPropertyDescriptor: tt, getOwnPropertyNames: ot, getOwnPropertySymbols: rt, getPrototypeOf: it } = Object, y = globalThis, ze = y.trustedTypes, at = ze ? ze.emptyScript : "", W = y.reactiveElementPolyfillSupport, I = (i, e) => i, Q = { toAttribute(i, e) {
  switch (e) {
    case Boolean:
      i = i ? at : null;
      break;
    case Object:
    case Array:
      i = i == null ? i : JSON.stringify(i);
  }
  return i;
}, fromAttribute(i, e) {
  let t = i;
  switch (e) {
    case Boolean:
      t = i !== null;
      break;
    case Number:
      t = i === null ? null : Number(i);
      break;
    case Object:
    case Array:
      try {
        t = JSON.parse(i);
      } catch {
        t = null;
      }
  }
  return t;
} }, De = (i, e) => !Je(i, e), Ce = { attribute: !0, type: String, converter: Q, reflect: !1, useDefault: !1, hasChanged: De };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), y.litPropertyMetadata ?? (y.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let C = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ?? (this.l = [])).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, t = Ce) {
    if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
      const o = Symbol(), r = this.getPropertyDescriptor(e, o, t);
      r !== void 0 && et(this.prototype, e, r);
    }
  }
  static getPropertyDescriptor(e, t, o) {
    const { get: r, set: a } = tt(this.prototype, e) ?? { get() {
      return this[t];
    }, set(s) {
      this[t] = s;
    } };
    return { get: r, set(s) {
      const u = r == null ? void 0 : r.call(this);
      a == null || a.call(this, s), this.requestUpdate(e, u, o);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? Ce;
  }
  static _$Ei() {
    if (this.hasOwnProperty(I("elementProperties"))) return;
    const e = it(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(I("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(I("properties"))) {
      const t = this.properties, o = [...ot(t), ...rt(t)];
      for (const r of o) this.createProperty(r, t[r]);
    }
    const e = this[Symbol.metadata];
    if (e !== null) {
      const t = litPropertyMetadata.get(e);
      if (t !== void 0) for (const [o, r] of t) this.elementProperties.set(o, r);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t, o] of this.elementProperties) {
      const r = this._$Eu(t, o);
      r !== void 0 && this._$Eh.set(r, t);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(e) {
    const t = [];
    if (Array.isArray(e)) {
      const o = new Set(e.flat(1 / 0).reverse());
      for (const r of o) t.unshift($e(r));
    } else e !== void 0 && t.push($e(e));
    return t;
  }
  static _$Eu(e, t) {
    const o = t.attribute;
    return o === !1 ? void 0 : typeof o == "string" ? o : typeof e == "string" ? e.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    var e;
    this._$ES = new Promise((t) => this.enableUpdating = t), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), (e = this.constructor.l) == null || e.forEach((t) => t(this));
  }
  addController(e) {
    var t;
    (this._$EO ?? (this._$EO = /* @__PURE__ */ new Set())).add(e), this.renderRoot !== void 0 && this.isConnected && ((t = e.hostConnected) == null || t.call(e));
  }
  removeController(e) {
    var t;
    (t = this._$EO) == null || t.delete(e);
  }
  _$E_() {
    const e = /* @__PURE__ */ new Map(), t = this.constructor.elementProperties;
    for (const o of t.keys()) this.hasOwnProperty(o) && (e.set(o, this[o]), delete this[o]);
    e.size > 0 && (this._$Ep = e);
  }
  createRenderRoot() {
    const e = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return Ge(e, this.constructor.elementStyles), e;
  }
  connectedCallback() {
    var e;
    this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this.enableUpdating(!0), (e = this._$EO) == null || e.forEach((t) => {
      var o;
      return (o = t.hostConnected) == null ? void 0 : o.call(t);
    });
  }
  enableUpdating(e) {
  }
  disconnectedCallback() {
    var e;
    (e = this._$EO) == null || e.forEach((t) => {
      var o;
      return (o = t.hostDisconnected) == null ? void 0 : o.call(t);
    });
  }
  attributeChangedCallback(e, t, o) {
    this._$AK(e, o);
  }
  _$ET(e, t) {
    var a;
    const o = this.constructor.elementProperties.get(e), r = this.constructor._$Eu(e, o);
    if (r !== void 0 && o.reflect === !0) {
      const s = (((a = o.converter) == null ? void 0 : a.toAttribute) !== void 0 ? o.converter : Q).toAttribute(t, o.type);
      this._$Em = e, s == null ? this.removeAttribute(r) : this.setAttribute(r, s), this._$Em = null;
    }
  }
  _$AK(e, t) {
    var a, s;
    const o = this.constructor, r = o._$Eh.get(e);
    if (r !== void 0 && this._$Em !== r) {
      const u = o.getPropertyOptions(r), l = typeof u.converter == "function" ? { fromAttribute: u.converter } : ((a = u.converter) == null ? void 0 : a.fromAttribute) !== void 0 ? u.converter : Q;
      this._$Em = r;
      const v = l.fromAttribute(t, u.type);
      this[r] = v ?? ((s = this._$Ej) == null ? void 0 : s.get(r)) ?? v, this._$Em = null;
    }
  }
  requestUpdate(e, t, o, r = !1, a) {
    var s;
    if (e !== void 0) {
      const u = this.constructor;
      if (r === !1 && (a = this[e]), o ?? (o = u.getPropertyOptions(e)), !((o.hasChanged ?? De)(a, t) || o.useDefault && o.reflect && a === ((s = this._$Ej) == null ? void 0 : s.get(e)) && !this.hasAttribute(u._$Eu(e, o)))) return;
      this.C(e, t, o);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, t, { useDefault: o, reflect: r, wrapped: a }, s) {
    o && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(e) && (this._$Ej.set(e, s ?? t ?? this[e]), a !== !0 || s !== void 0) || (this._$AL.has(e) || (this.hasUpdated || o || (t = void 0), this._$AL.set(e, t)), r === !0 && this._$Em !== e && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(e));
  }
  async _$EP() {
    this.isUpdatePending = !0;
    try {
      await this._$ES;
    } catch (t) {
      Promise.reject(t);
    }
    const e = this.scheduleUpdate();
    return e != null && await e, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    var o;
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this._$Ep) {
        for (const [a, s] of this._$Ep) this[a] = s;
        this._$Ep = void 0;
      }
      const r = this.constructor.elementProperties;
      if (r.size > 0) for (const [a, s] of r) {
        const { wrapped: u } = s, l = this[a];
        u !== !0 || this._$AL.has(a) || l === void 0 || this.C(a, void 0, s, l);
      }
    }
    let e = !1;
    const t = this._$AL;
    try {
      e = this.shouldUpdate(t), e ? (this.willUpdate(t), (o = this._$EO) == null || o.forEach((r) => {
        var a;
        return (a = r.hostUpdate) == null ? void 0 : a.call(r);
      }), this.update(t)) : this._$EM();
    } catch (r) {
      throw e = !1, this._$EM(), r;
    }
    e && this._$AE(t);
  }
  willUpdate(e) {
  }
  _$AE(e) {
    var t;
    (t = this._$EO) == null || t.forEach((o) => {
      var r;
      return (r = o.hostUpdated) == null ? void 0 : r.call(o);
    }), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(e)), this.updated(e);
  }
  _$EM() {
    this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = !1;
  }
  get updateComplete() {
    return this.getUpdateComplete();
  }
  getUpdateComplete() {
    return this._$ES;
  }
  shouldUpdate(e) {
    return !0;
  }
  update(e) {
    this._$Eq && (this._$Eq = this._$Eq.forEach((t) => this._$ET(t, this[t]))), this._$EM();
  }
  updated(e) {
  }
  firstUpdated(e) {
  }
};
C.elementStyles = [], C.shadowRootOptions = { mode: "open" }, C[I("elementProperties")] = /* @__PURE__ */ new Map(), C[I("finalized")] = /* @__PURE__ */ new Map(), W == null || W({ ReactiveElement: C }), (y.reactiveElementVersions ?? (y.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const j = globalThis, Se = (i) => i, U = j.trustedTypes, Ae = U ? U.createPolicy("lit-html", { createHTML: (i) => i }) : void 0, Ve = "$lit$", x = `lit$${Math.random().toFixed(9).slice(2)}$`, Ne = "?" + x, st = `<${Ne}>`, z = document, T = () => z.createComment(""), M = (i) => i === null || typeof i != "object" && typeof i != "function", ke = Array.isArray, nt = (i) => ke(i) || typeof (i == null ? void 0 : i[Symbol.iterator]) == "function", K = `[ 	
\f\r]`, E = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, Ee = /-->/g, Ie = />/g, k = RegExp(`>|${K}(?:([^\\s"'>=/]+)(${K}*=${K}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), je = /'/g, Te = /"/g, Pe = /^(?:script|style|textarea|title)$/i, lt = (i) => (e, ...t) => ({ _$litType$: i, strings: e, values: t }), c = lt(1), S = Symbol.for("lit-noChange"), d = Symbol.for("lit-nothing"), Me = /* @__PURE__ */ new WeakMap(), _ = z.createTreeWalker(z, 129);
function Re(i, e) {
  if (!ke(i) || !i.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return Ae !== void 0 ? Ae.createHTML(e) : e;
}
const ct = (i, e) => {
  const t = i.length - 1, o = [];
  let r, a = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", s = E;
  for (let u = 0; u < t; u++) {
    const l = i[u];
    let v, f, m = -1, g = 0;
    for (; g < l.length && (s.lastIndex = g, f = s.exec(l), f !== null); ) g = s.lastIndex, s === E ? f[1] === "!--" ? s = Ee : f[1] !== void 0 ? s = Ie : f[2] !== void 0 ? (Pe.test(f[2]) && (r = RegExp("</" + f[2], "g")), s = k) : f[3] !== void 0 && (s = k) : s === k ? f[0] === ">" ? (s = r ?? E, m = -1) : f[1] === void 0 ? m = -2 : (m = s.lastIndex - f[2].length, v = f[1], s = f[3] === void 0 ? k : f[3] === '"' ? Te : je) : s === Te || s === je ? s = k : s === Ee || s === Ie ? s = E : (s = k, r = void 0);
    const w = s === k && i[u + 1].startsWith("/>") ? " " : "";
    a += s === E ? l + st : m >= 0 ? (o.push(v), l.slice(0, m) + Ve + l.slice(m) + x + w) : l + x + (m === -2 ? u : w);
  }
  return [Re(i, a + (i[t] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), o];
};
class O {
  constructor({ strings: e, _$litType$: t }, o) {
    let r;
    this.parts = [];
    let a = 0, s = 0;
    const u = e.length - 1, l = this.parts, [v, f] = ct(e, t);
    if (this.el = O.createElement(v, o), _.currentNode = this.el.content, t === 2 || t === 3) {
      const m = this.el.content.firstChild;
      m.replaceWith(...m.childNodes);
    }
    for (; (r = _.nextNode()) !== null && l.length < u; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const m of r.getAttributeNames()) if (m.endsWith(Ve)) {
          const g = f[s++], w = r.getAttribute(m).split(x), B = /([.?@])?(.*)/.exec(g);
          l.push({ type: 1, index: a, name: B[2], strings: w, ctor: B[1] === "." ? pt : B[1] === "?" ? ut : B[1] === "@" ? ht : F }), r.removeAttribute(m);
        } else m.startsWith(x) && (l.push({ type: 6, index: a }), r.removeAttribute(m));
        if (Pe.test(r.tagName)) {
          const m = r.textContent.split(x), g = m.length - 1;
          if (g > 0) {
            r.textContent = U ? U.emptyScript : "";
            for (let w = 0; w < g; w++) r.append(m[w], T()), _.nextNode(), l.push({ type: 2, index: ++a });
            r.append(m[g], T());
          }
        }
      } else if (r.nodeType === 8) if (r.data === Ne) l.push({ type: 2, index: a });
      else {
        let m = -1;
        for (; (m = r.data.indexOf(x, m + 1)) !== -1; ) l.push({ type: 7, index: a }), m += x.length - 1;
      }
      a++;
    }
  }
  static createElement(e, t) {
    const o = z.createElement("template");
    return o.innerHTML = e, o;
  }
}
function A(i, e, t = i, o) {
  var s, u;
  if (e === S) return e;
  let r = o !== void 0 ? (s = t._$Co) == null ? void 0 : s[o] : t._$Cl;
  const a = M(e) ? void 0 : e._$litDirective$;
  return (r == null ? void 0 : r.constructor) !== a && ((u = r == null ? void 0 : r._$AO) == null || u.call(r, !1), a === void 0 ? r = void 0 : (r = new a(i), r._$AT(i, t, o)), o !== void 0 ? (t._$Co ?? (t._$Co = []))[o] = r : t._$Cl = r), r !== void 0 && (e = A(i, r._$AS(i, e.values), r, o)), e;
}
class dt {
  constructor(e, t) {
    this._$AV = [], this._$AN = void 0, this._$AD = e, this._$AM = t;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(e) {
    const { el: { content: t }, parts: o } = this._$AD, r = ((e == null ? void 0 : e.creationScope) ?? z).importNode(t, !0);
    _.currentNode = r;
    let a = _.nextNode(), s = 0, u = 0, l = o[0];
    for (; l !== void 0; ) {
      if (s === l.index) {
        let v;
        l.type === 2 ? v = new q(a, a.nextSibling, this, e) : l.type === 1 ? v = new l.ctor(a, l.name, l.strings, this, e) : l.type === 6 && (v = new bt(a, this, e)), this._$AV.push(v), l = o[++u];
      }
      s !== (l == null ? void 0 : l.index) && (a = _.nextNode(), s++);
    }
    return _.currentNode = z, r;
  }
  p(e) {
    let t = 0;
    for (const o of this._$AV) o !== void 0 && (o.strings !== void 0 ? (o._$AI(e, o, t), t += o.strings.length - 2) : o._$AI(e[t])), t++;
  }
}
class q {
  get _$AU() {
    var e;
    return ((e = this._$AM) == null ? void 0 : e._$AU) ?? this._$Cv;
  }
  constructor(e, t, o, r) {
    this.type = 2, this._$AH = d, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = o, this.options = r, this._$Cv = (r == null ? void 0 : r.isConnected) ?? !0;
  }
  get parentNode() {
    let e = this._$AA.parentNode;
    const t = this._$AM;
    return t !== void 0 && (e == null ? void 0 : e.nodeType) === 11 && (e = t.parentNode), e;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(e, t = this) {
    e = A(this, e, t), M(e) ? e === d || e == null || e === "" ? (this._$AH !== d && this._$AR(), this._$AH = d) : e !== this._$AH && e !== S && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : nt(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== d && M(this._$AH) ? this._$AA.nextSibling.data = e : this.T(z.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    var a;
    const { values: t, _$litType$: o } = e, r = typeof o == "number" ? this._$AC(e) : (o.el === void 0 && (o.el = O.createElement(Re(o.h, o.h[0]), this.options)), o);
    if (((a = this._$AH) == null ? void 0 : a._$AD) === r) this._$AH.p(t);
    else {
      const s = new dt(r, this), u = s.u(this.options);
      s.p(t), this.T(u), this._$AH = s;
    }
  }
  _$AC(e) {
    let t = Me.get(e.strings);
    return t === void 0 && Me.set(e.strings, t = new O(e)), t;
  }
  k(e) {
    ke(this._$AH) || (this._$AH = [], this._$AR());
    const t = this._$AH;
    let o, r = 0;
    for (const a of e) r === t.length ? t.push(o = new q(this.O(T()), this.O(T()), this, this.options)) : o = t[r], o._$AI(a), r++;
    r < t.length && (this._$AR(o && o._$AB.nextSibling, r), t.length = r);
  }
  _$AR(e = this._$AA.nextSibling, t) {
    var o;
    for ((o = this._$AP) == null ? void 0 : o.call(this, !1, !0, t); e !== this._$AB; ) {
      const r = Se(e).nextSibling;
      Se(e).remove(), e = r;
    }
  }
  setConnected(e) {
    var t;
    this._$AM === void 0 && (this._$Cv = e, (t = this._$AP) == null || t.call(this, e));
  }
}
class F {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(e, t, o, r, a) {
    this.type = 1, this._$AH = d, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = a, o.length > 2 || o[0] !== "" || o[1] !== "" ? (this._$AH = Array(o.length - 1).fill(new String()), this.strings = o) : this._$AH = d;
  }
  _$AI(e, t = this, o, r) {
    const a = this.strings;
    let s = !1;
    if (a === void 0) e = A(this, e, t, 0), s = !M(e) || e !== this._$AH && e !== S, s && (this._$AH = e);
    else {
      const u = e;
      let l, v;
      for (e = a[0], l = 0; l < a.length - 1; l++) v = A(this, u[o + l], t, l), v === S && (v = this._$AH[l]), s || (s = !M(v) || v !== this._$AH[l]), v === d ? e = d : e !== d && (e += (v ?? "") + a[l + 1]), this._$AH[l] = v;
    }
    s && !r && this.j(e);
  }
  j(e) {
    e === d ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class pt extends F {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === d ? void 0 : e;
  }
}
class ut extends F {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== d);
  }
}
class ht extends F {
  constructor(e, t, o, r, a) {
    super(e, t, o, r, a), this.type = 5;
  }
  _$AI(e, t = this) {
    if ((e = A(this, e, t, 0) ?? d) === S) return;
    const o = this._$AH, r = e === d && o !== d || e.capture !== o.capture || e.once !== o.once || e.passive !== o.passive, a = e !== d && (o === d || r);
    r && this.element.removeEventListener(this.name, this, o), a && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    var t;
    typeof this._$AH == "function" ? this._$AH.call(((t = this.options) == null ? void 0 : t.host) ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class bt {
  constructor(e, t, o) {
    this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = o;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(e) {
    A(this, e);
  }
}
const Z = j.litHtmlPolyfillSupport;
Z == null || Z(O, q), (j.litHtmlVersions ?? (j.litHtmlVersions = [])).push("3.3.3");
const mt = (i, e, t) => {
  const o = (t == null ? void 0 : t.renderBefore) ?? e;
  let r = o._$litPart$;
  if (r === void 0) {
    const a = (t == null ? void 0 : t.renderBefore) ?? null;
    o._$litPart$ = r = new q(e.insertBefore(T(), a), a, void 0, t ?? {});
  }
  return r._$AI(i), r;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const $ = globalThis;
class p extends C {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    var t;
    const e = super.createRenderRoot();
    return (t = this.renderOptions).renderBefore ?? (t.renderBefore = e.firstChild), e;
  }
  update(e) {
    const t = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = mt(t, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    var e;
    super.connectedCallback(), (e = this._$Do) == null || e.setConnected(!0);
  }
  disconnectedCallback() {
    var e;
    super.disconnectedCallback(), (e = this._$Do) == null || e.setConnected(!1);
  }
  render() {
    return S;
  }
}
var Oe;
p._$litElement$ = !0, p.finalized = !0, (Oe = $.litElementHydrateSupport) == null || Oe.call($, { LitElement: p });
const X = $.litElementPolyfillSupport;
X == null || X({ LitElement: p });
($.litElementVersions ?? ($.litElementVersions = [])).push("4.2.2");
const b = new CSSStyleSheet();
b.replaceSync(qe);
class G extends p {
  constructor() {
    super(), this.variant = "scrollable";
  }
  render() {
    return c`
      <a href="#u-page-main" class="skip-link">Skip to main content</a>
      <main id="u-page-main"><slot></slot></main>
    `;
  }
}
n(G, "styles", [
  b,
  h`
      :host {
        display: block;
        min-height: 100vh;
        background-color: var(--color-base-200);
      }
      :host([variant='fixed']) {
        height: 100vh;
        min-height: 0;
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }
      /* The host is the flex column, but its only in-flow child is <main>.
         Make <main> fill the host and be the flex column itself so the slotted
         page sections become its flex items — otherwise a block <main> sizes to
         its content, overflows the 100vh host, and leaves grow/scroll children
         with no bounded height. */
      :host([variant='fixed']) main {
        flex: 1;
        min-height: 0;
        display: flex;
        flex-direction: column;
      }
      .skip-link {
        position: absolute;
        top: -100%;
        left: calc(var(--spacing) * 4);
        z-index: 9999;
        padding: calc(var(--spacing) * 2) calc(var(--spacing) * 4);
        background: var(--color-base-100);
        color: var(--color-base-content);
        border-radius: var(--radius-btn);
        text-decoration: none;
        font-weight: 600;
      }
      .skip-link:focus-visible {
        top: calc(var(--spacing) * 4);
      }
    `
]), n(G, "properties", {
  variant: { type: String, reflect: !0 }
});
customElements.define("u-page", G);
class J extends p {
  constructor() {
    super(), this.grow = !1, this.scroll = !1;
  }
  render() {
    return c`<div class="container mx-auto px-4"><slot></slot></div>`;
  }
}
n(J, "styles", [
  b,
  h`
      :host {
        display: block;
      }
      :host([grow]) {
        flex: 1 1 0;
        min-height: 0;
      }
      :host([grow]) div {
        display: flex;
        flex-direction: column;
        height: 100%;
      }
      :host([scroll]) {
        overflow-y: auto;
        min-height: 0;
      }
    `
]), n(J, "properties", {
  grow: { type: Boolean, reflect: !0 },
  scroll: { type: Boolean, reflect: !0 }
});
customElements.define("u-container", J);
class ee extends p {
  constructor() {
    super(), this.gap = "md", this.align = "center", this.justify = "start", this.wrap = !1, this.grow = !1, this.scroll = !1;
  }
  render() {
    return c`<slot></slot>`;
  }
}
n(ee, "styles", [
  b,
  h`
      :host {
        display: flex;
        flex-direction: row;
        gap: calc(var(--spacing) * 4);
        align-items: center;
        justify-content: flex-start;
        flex-wrap: nowrap;
      }

      :host([gap='none']) {
        gap: 0;
      }
      :host([gap='xs']) {
        gap: calc(var(--spacing) * 1);
      }
      :host([gap='sm']) {
        gap: calc(var(--spacing) * 2);
      }
      :host([gap='md']) {
        gap: calc(var(--spacing) * 4);
      }
      :host([gap='lg']) {
        gap: calc(var(--spacing) * 6);
      }
      :host([gap='xl']) {
        gap: calc(var(--spacing) * 8);
      }

      :host([align='start']) {
        align-items: flex-start;
      }
      :host([align='center']) {
        align-items: center;
      }
      :host([align='end']) {
        align-items: flex-end;
      }
      :host([align='stretch']) {
        align-items: stretch;
      }
      :host([align='baseline']) {
        align-items: baseline;
      }

      :host([justify='start']) {
        justify-content: flex-start;
      }
      :host([justify='center']) {
        justify-content: center;
      }
      :host([justify='end']) {
        justify-content: flex-end;
      }
      :host([justify='between']) {
        justify-content: space-between;
      }
      :host([justify='around']) {
        justify-content: space-around;
      }

      :host([wrap]) {
        flex-wrap: wrap;
      }

      /* Longhands rather than the flex shorthand: only flex-basis depends on
         --spacing, so grow/shrink still apply if the token is missing. */
      :host([basis='sm']),
      :host([basis='md']),
      :host([basis='lg']) {
        flex-grow: 0;
        flex-shrink: 0;
        min-width: 0;
        min-height: 0;
      }
      :host([basis='sm']) {
        flex-basis: calc(var(--spacing) * 64);
      }
      :host([basis='md']) {
        flex-basis: calc(var(--spacing) * 80);
      }
      :host([basis='lg']) {
        flex-basis: calc(var(--spacing) * 96);
      }

      /* After basis, so the flex shorthand resets it when both are set. */
      :host([grow]) {
        flex: 1 1 0;
        min-height: 0;
        min-width: 0;
      }

      :host([scroll]) {
        overflow-x: auto;
        min-width: 0;
      }
    `
]), n(ee, "properties", {
  gap: { type: String, reflect: !0 },
  align: { type: String, reflect: !0 },
  justify: { type: String, reflect: !0 },
  wrap: { type: Boolean, reflect: !0 },
  basis: { type: String, reflect: !0 },
  grow: { type: Boolean, reflect: !0 },
  scroll: { type: Boolean, reflect: !0 }
});
customElements.define("u-hstack", ee);
class te extends p {
  constructor() {
    super(), this.gap = "md", this.align = "stretch", this.justify = "start", this.grow = !1, this.scroll = !1;
  }
  render() {
    return c`<slot></slot>`;
  }
}
n(te, "styles", [
  b,
  h`
      :host {
        display: flex;
        flex-direction: column;
        gap: calc(var(--spacing) * 4);
        align-items: stretch;
        justify-content: flex-start;
      }

      :host([gap='none']) {
        gap: 0;
      }
      :host([gap='xs']) {
        gap: calc(var(--spacing) * 1);
      }
      :host([gap='sm']) {
        gap: calc(var(--spacing) * 2);
      }
      :host([gap='md']) {
        gap: calc(var(--spacing) * 4);
      }
      :host([gap='lg']) {
        gap: calc(var(--spacing) * 6);
      }
      :host([gap='xl']) {
        gap: calc(var(--spacing) * 8);
      }

      :host([align='start']) {
        align-items: flex-start;
      }
      :host([align='center']) {
        align-items: center;
      }
      :host([align='end']) {
        align-items: flex-end;
      }
      :host([align='stretch']) {
        align-items: stretch;
      }

      :host([justify='start']) {
        justify-content: flex-start;
      }
      :host([justify='center']) {
        justify-content: center;
      }
      :host([justify='end']) {
        justify-content: flex-end;
      }
      :host([justify='between']) {
        justify-content: space-between;
      }

      /* Longhands rather than the flex shorthand: only flex-basis depends on
         --spacing, so grow/shrink still apply if the token is missing. */
      :host([basis='sm']),
      :host([basis='md']),
      :host([basis='lg']) {
        flex-grow: 0;
        flex-shrink: 0;
        min-width: 0;
        min-height: 0;
      }
      :host([basis='sm']) {
        flex-basis: calc(var(--spacing) * 64);
      }
      :host([basis='md']) {
        flex-basis: calc(var(--spacing) * 80);
      }
      :host([basis='lg']) {
        flex-basis: calc(var(--spacing) * 96);
      }

      /* After basis, so the flex shorthand resets it when both are set.
         min-width too, as <u-hstack grow> already does: a grow stack is often a
         column inside a row, and without it the stack refuses to shrink below
         its widest child — a wide table then pushes the page sideways instead
         of scrolling inside its own region. */
      :host([grow]) {
        flex: 1 1 0;
        min-height: 0;
        min-width: 0;
      }

      :host([scroll]) {
        overflow-y: auto;
        min-height: 0;
      }
    `
]), n(te, "properties", {
  gap: { type: String, reflect: !0 },
  align: { type: String, reflect: !0 },
  justify: { type: String, reflect: !0 },
  basis: { type: String, reflect: !0 },
  grow: { type: Boolean, reflect: !0 },
  scroll: { type: Boolean, reflect: !0 }
});
customElements.define("u-vstack", te);
class He extends p {
  connectedCallback() {
    super.connectedCallback(), this.setAttribute("aria-hidden", "true");
  }
}
n(He, "styles", h`
    :host {
      display: block;
      flex: 1;
    }
  `);
customElements.define("u-spacer", He);
class Le extends p {
  render() {
    return c`
      <header class="py-4">
        <h1 class="text-2xl font-semibold m-0"><slot></slot></h1>
      </header>
    `;
  }
}
n(Le, "styles", [
  b,
  h`
      :host {
        display: block;
      }
    `
]);
customElements.define("u-page-header", Le);
class oe extends p {
  constructor() {
    super(), this.grow = !1, this.tone = "", this.dismissible = !1, this._hasTitle = !1;
  }
  _onTitleSlotChange(e) {
    this._hasTitle = e.target.assignedNodes({ flatten: !0 }).length > 0;
  }
  _dismiss() {
    this.dispatchEvent(new CustomEvent("u-close", { bubbles: !0, composed: !0 }));
  }
  render() {
    return c`
      <div class="card shadow-sm${this.tone ? "" : " bg-base-100"}">
        <div class="card-body">
          <!-- A real flex row, not an absolutely-positioned button: it makes
               room for the title instead of risking an overlap with a long
               one. ml-auto (not justify-between on the row) keeps the button
               pinned right even when there is no title to space against. -->
          <div class="flex items-start gap-3" ?hidden="${!this._hasTitle && !this.dismissible}">
            <div class="card-title text-base" ?hidden="${!this._hasTitle}">
              <slot name="title" @slotchange="${this._onTitleSlotChange}"></slot>
            </div>
            ${this.dismissible ? c`
                  <button
                    type="button"
                    class="u-dismiss-btn btn btn-ghost btn-sm btn-square rounded-box ml-auto shrink-0"
                    aria-label="Dismiss"
                    @click="${this._dismiss}"
                  >
                    ✕
                  </button>
                ` : d}
          </div>
          <slot></slot>
        </div>
      </div>
    `;
  }
}
n(oe, "styles", [
  b,
  h`
      :host {
        display: block;
      }
      /* The card's own wrappers are flex columns already; they only need to be
         told to fill rather than shrink-wrap, or a scrolling child inside a
         fixed page has no bounded height to scroll within. */
      :host([grow]) {
        display: flex;
        flex-direction: column;
        flex: 1 1 0;
        min-height: 0;
        min-width: 0;
      }
      :host([grow]) .card,
      :host([grow]) .card-body {
        flex: 1 1 0;
        min-height: 0;
        min-width: 0;
      }
      /* One static rule per tone: a runtime-composed "bg-" plus tone class
         would be invisible to Tailwind's static extraction and emit no CSS
         at all (daisyUI's alert-variant/badge-variant classes are safe to
         interpolate because they ship as full component CSS regardless of
         usage; plain Tailwind color utilities are not). Text stays
         --color-base-content across every tone rather than switching to the
         paired -content color (e.g. --color-error-content) — DaisyUI's own
         pairing reads harder to scan at this size than a plain dark/light
         text color on a tinted surface. */
      :host([tone]) .card {
        color: var(--color-base-content);
      }
      :host([tone='info']) .card {
        background-color: var(--color-info);
      }
      :host([tone='success']) .card {
        background-color: var(--color-success);
      }
      :host([tone='warning']) .card {
        background-color: var(--color-warning);
      }
      :host([tone='error']) .card {
        background-color: var(--color-error);
      }
    `
]), n(oe, "properties", {
  grow: { type: Boolean, reflect: !0 },
  tone: { type: String, reflect: !0 },
  dismissible: { type: Boolean, reflect: !0 },
  _hasTitle: { state: !0 }
});
customElements.define("u-card", oe);
const Y = ["action", "method", "enctype", "novalidate", "autocomplete", "target"], vt = ["grow"], ft = ["style", "class"], Ue = new CSSStyleSheet();
Ue.replaceSync(`
  u-form {
    display: block;
  }
  u-form[grow] {
    display: flex;
    flex-direction: column;
    flex: 1 1 0;
    min-height: 0;
    min-width: 0;
  }
  /* The inner <form> is the flex item that fills the host, so children with a
     grow of their own divide the host's height between them. min-width keeps a
     horizontally-scrolling child from widening the form past its column. */
  u-form[grow] > form {
    flex: 1 1 0;
    min-height: 0;
    min-width: 0;
  }
`);
document.adoptedStyleSheets = [...document.adoptedStyleSheets, Ue];
class gt extends HTMLElement {
  connectedCallback() {
    if (!this._initialized) {
      this._initialized = !0, this._selfRemovals = /* @__PURE__ */ new Set(), this._form = document.createElement("form"), this._form.className = "flex flex-col", this._form.style.gap = "calc(var(--spacing) * 4)";
      for (const { name: e, value: t } of [...this.attributes])
        e.startsWith("hx-") ? (this._form.setAttribute(e, t), this.removeAttribute(e)) : Y.includes(e) && this._form.setAttribute(e, t);
      for (; this.firstChild; )
        this._form.appendChild(this.firstChild);
      this.appendChild(this._form), this._childObserver = new MutationObserver((e) => {
        for (const t of e)
          for (const o of t.addedNodes)
            o !== this._form && this._form.appendChild(o);
      }), this._childObserver.observe(this, { childList: !0 }), this._attrObserver = new MutationObserver((e) => {
        for (const t of e) {
          const o = t.attributeName;
          if (!o || this._selfRemovals.delete(o) || ft.includes(o) || vt.includes(o)) continue;
          if (!Y.includes(o) && !o.startsWith("hx-")) {
            console.warn(
              `[u-form] Attribute "${o}" is not forwarded to the inner <form>. Supported attributes: ${Y.join(", ")}, hx-*.`
            );
            continue;
          }
          const r = this.getAttribute(o);
          r === null ? this._form.removeAttribute(o) : (this._form.setAttribute(o, r), o.startsWith("hx-") && (this._selfRemovals.add(o), this.removeAttribute(o)));
        }
      }), this._attrObserver.observe(this, { attributes: !0 }), window.htmx && window.htmx.process(this._form);
    }
  }
  disconnectedCallback() {
    var e, t;
    (e = this._childObserver) == null || e.disconnect(), (t = this._attrObserver) == null || t.disconnect();
  }
}
customElements.define("u-form", gt);
class V extends p {
  constructor() {
    super(), this._internals = this.attachInternals(), this.variant = "neutral", this.size = "md", this.circle = !1, this.pressed = !1, this.disabled = !1, this.loading = !1, this.href = "", this.type = "button";
  }
  get _safeHref() {
    const e = this.href ?? "";
    return /^javascript:/i.test(e) ? "#" : e;
  }
  get _isInert() {
    return this.disabled || this.loading;
  }
  _classes(e = !1) {
    const t = ["btn", `btn-${this.variant}`];
    return this.size === "sm" && t.push("btn-sm"), this.size === "lg" && t.push("btn-lg"), this.circle && t.push("btn-circle"), this.pressed && t.push("btn-active"), e && t.push("btn-disabled"), t.join(" ");
  }
  _handleClick(e) {
    var t, o;
    if (this._isInert) {
      e.stopPropagation();
      return;
    }
    this.type === "submit" ? (t = this._internals.form) == null || t.requestSubmit() : this.type === "reset" && ((o = this._internals.form) == null || o.reset());
  }
  _handleAnchorClick(e) {
    this.disabled && (e.preventDefault(), e.stopPropagation());
  }
  render() {
    return this.href ? c`
        <a
          href="${this._safeHref}"
          class="${this._classes(this.disabled)}"
          aria-disabled="${this.disabled ? "true" : d}"
          @click="${this._handleAnchorClick}"
        >
          <slot></slot>
        </a>
      ` : c`
      <button
        type="button"
        class="${this._classes(this._isInert)} rounded-box"
        aria-disabled="${this._isInert ? "true" : d}"
        aria-busy="${this.loading ? "true" : d}"
        aria-pressed="${this.pressed ? "true" : d}"
        @click="${this._handleClick}"
      >
        ${this.loading ? c`<span class="loading loading-spinner loading-sm" aria-hidden="true"></span>` : d}
        <slot></slot>
      </button>
    `;
  }
}
n(V, "formAssociated", !0), n(V, "styles", [
  b,
  h`
      :host {
        display: inline-block;
      }
    `
]), n(V, "properties", {
  variant: { type: String, reflect: !0 },
  size: { type: String, reflect: !0 },
  circle: { type: Boolean, reflect: !0 },
  pressed: { type: Boolean, reflect: !0 },
  disabled: { type: Boolean, reflect: !0 },
  loading: { type: Boolean, reflect: !0 },
  href: { type: String },
  type: { type: String }
});
customElements.define("u-button", V);
class N extends p {
  constructor() {
    super(), this._internals = this.attachInternals(), this.name = "", this.value = "on", this.uncheckedValue = null, this.checked = !1, this.required = !1, this.disabled = !1, this.size = "md", this.indeterminate = !1, this._internals.setFormValue(null);
  }
  connectedCallback() {
    this._defaultChecked === void 0 && (this._defaultChecked = this.hasAttribute("checked")), super.connectedCallback();
  }
  updated(e) {
    (e.has("checked") || e.has("value") || e.has("uncheckedValue")) && this._internals.setFormValue(this.checked ? this.value : this.uncheckedValue ?? null), e.has("indeterminate") && (this.shadowRoot.querySelector("input").indeterminate = this.indeterminate), ["checked", "required", "disabled"].some((t) => e.has(t)) && this._syncValidity();
  }
  formResetCallback() {
    this.checked = this._defaultChecked ?? !1;
  }
  _syncValidity() {
    const e = this.shadowRoot.querySelector("input");
    e.checkValidity() ? this._internals.setValidity({}) : this._internals.setValidity(e.validity, e.validationMessage, e);
  }
  _onChange(e) {
    this.checked = e.target.checked, this.dispatchEvent(new Event("change", { bubbles: !0, composed: !0 }));
  }
  get _classes() {
    const e = ["checkbox"];
    return this.size === "sm" && e.push("checkbox-sm"), this.size === "lg" && e.push("checkbox-lg"), e.join(" ");
  }
  render() {
    return c`
      <input
        type="checkbox"
        class="${this._classes}"
        .checked="${this.checked}"
        ?required="${this.required}"
        ?disabled="${this.disabled}"
        @change="${this._onChange}"
      />
    `;
  }
}
n(N, "formAssociated", !0), n(N, "styles", [
  b,
  h`
      :host {
        display: inline-block;
      }
    `
]), n(N, "properties", {
  name: { type: String, reflect: !0 },
  value: { type: String },
  uncheckedValue: { type: String, attribute: "unchecked-value" },
  checked: { type: Boolean, reflect: !0 },
  required: { type: Boolean, reflect: !0 },
  disabled: { type: Boolean, reflect: !0 },
  size: { type: String, reflect: !0 },
  indeterminate: { type: Boolean }
});
customElements.define("u-checkbox", N);
class re extends p {
  constructor() {
    super(), this.confirmed = !1, this.disabled = !1, this.actionAlign = "start", this._checkboxId = `uca-${Math.random().toString(36).slice(2, 9)}`;
  }
  get _gateClosed() {
    return this.disabled || !this.confirmed;
  }
  _onCheckboxChange(e) {
    this.confirmed = e.target.checked, this.dispatchEvent(
      new CustomEvent("u-change", {
        detail: { confirmed: this.confirmed },
        bubbles: !0,
        composed: !0
      })
    );
  }
  _onActionSlotChange(e) {
    this._actionSlot = e.target, this._syncActionDisabled();
  }
  _syncActionDisabled() {
    var t;
    const e = this._gateClosed;
    for (const o of ((t = this._actionSlot) == null ? void 0 : t.assignedElements()) ?? [])
      "disabled" in o && (o.disabled = e);
  }
  updated(e) {
    (e.has("confirmed") || e.has("disabled")) && this._syncActionDisabled();
  }
  // The action row holds both slots so the gated control can stay last, which a
  // consumer cannot arrange from outside: a button placed after this component
  // lands after the whole block, not after the action. `w-full` keeps the default
  // `start` alignment looking exactly as it did before the row existed.
  render() {
    return c`
      <div class="flex flex-col items-start gap-3">
        <label
          for="${this._checkboxId}"
          class="flex items-start gap-2 cursor-pointer select-none"
          @click="${(e) => e.stopPropagation()}"
        >
          <input
            id="${this._checkboxId}"
            type="checkbox"
            class="checkbox"
            .checked="${this.confirmed}"
            ?disabled="${this.disabled}"
            @change="${this._onCheckboxChange}"
          />
          <span><slot name="confirmation-label"></slot></span>
        </label>
        <div
          class="flex w-full items-center gap-3 ${this.actionAlign === "end" ? "justify-end" : "justify-start"}"
        >
          <slot name="secondary-action"></slot>
          <slot name="action" @slotchange="${this._onActionSlotChange}"></slot>
        </div>
      </div>
    `;
  }
}
n(re, "styles", [
  b,
  h`
      :host {
        display: block;
      }
    `
]), n(re, "properties", {
  confirmed: { type: Boolean, reflect: !0 },
  disabled: { type: Boolean, reflect: !0 },
  actionAlign: { type: String, attribute: "action-align", reflect: !0 }
});
customElements.define("u-confirm-action", re);
class ie extends p {
  constructor() {
    super(), this.label = "", this.required = !1, this.spacer = !1, this.hint = "", this.error = "", this._uid = `uff-${Math.random().toString(36).slice(2, 9)}`, this.addEventListener("input", () => {
      this.error = "";
    });
  }
  _applyErrorState() {
    var a;
    const e = (a = this.shadowRoot) == null ? void 0 : a.querySelector("slot");
    if (!e) return;
    const t = e.assignedElements({ flatten: !0 });
    t.flatMap(
      (s) => ["INPUT", "SELECT", "TEXTAREA"].includes(s.tagName) ? [s] : [...s.querySelectorAll("input, select, textarea")]
    ).forEach((s) => s.classList.toggle("input-error", !!this.error)), t.flatMap(
      (s) => ["U-INPUT", "U-COMBOBOX", "U-MULTISELECT", "U-LIST-SELECT"].includes(s.tagName) ? [s] : [...s.querySelectorAll("u-input, u-combobox, u-multiselect, u-list-select")]
    ).forEach((s) => s.toggleAttribute("error", !!this.error));
  }
  _wireAria() {
    var u;
    const e = (u = this.shadowRoot) == null ? void 0 : u.querySelector("slot");
    if (!e) return;
    const o = e.assignedElements({ flatten: !0 }).flatMap(
      (l) => ["INPUT", "SELECT", "TEXTAREA"].includes(l.tagName) ? [l] : [...l.querySelectorAll("input, select, textarea")]
    ), r = [], a = this.shadowRoot.querySelector(".fieldset-label:not(.text-error)"), s = this.shadowRoot.querySelector(".fieldset-label.text-error");
    a && (a.id || (a.id = `${this._uid}-hint`), r.push(a.id)), s && (s.id || (s.id = `${this._uid}-error`), r.push(s.id)), o.forEach((l) => {
      r.length ? l.setAttribute("aria-describedby", r.join(" ")) : l.removeAttribute("aria-describedby"), this.required ? l.setAttribute("aria-required", "true") : l.removeAttribute("aria-required");
    });
  }
  updated(e) {
    e.has("error") && this._applyErrorState(), this._wireAria();
  }
  render() {
    return c`
      <fieldset class="fieldset">
        <legend class="fieldset-legend pl-1 pb-1" aria-hidden="${this.spacer ? "true" : d}">
          ${this.spacer ? c`&nbsp;` : c`${this.label}
              ${this.required ? c`<span aria-hidden="true" class="text-error ml-1">*</span>` : ""}`}
        </legend>
        <slot
          @slotchange="${() => {
      this._applyErrorState(), this._wireAria();
    }}"
        ></slot>
        ${this.hint && !this.error ? c`<p class="fieldset-label">${this.hint}</p>` : ""}
        ${this.error ? c`<p class="fieldset-label text-error">${this.error}</p>` : ""}
      </fieldset>
    `;
  }
}
n(ie, "styles", [
  b,
  h`
      :host {
        display: block;
      }
    `
]), n(ie, "properties", {
  label: { type: String },
  required: { type: Boolean, reflect: !0 },
  spacer: { type: Boolean, reflect: !0 },
  hint: { type: String },
  error: { type: String, reflect: !0 }
});
customElements.define("u-form-field", ie);
class P extends p {
  constructor() {
    super(), this._internals = this.attachInternals(), this.name = "", this.type = "text", this.placeholder = "", this.value = "", this.required = !1, this.pattern = "", this.autocomplete = "", this.disabled = !1, this.readonly = !1, this.error = !1, this._internals.setFormValue("");
  }
  connectedCallback() {
    this._defaultValue === void 0 && (this._defaultValue = this.getAttribute("value") ?? ""), super.connectedCallback();
  }
  firstUpdated() {
    this._syncValidity();
  }
  updated(e) {
    e.has("value") && this._internals.setFormValue(this.value), ["value", "required", "pattern", "disabled"].some((t) => e.has(t)) && this._syncValidity();
  }
  formResetCallback() {
    this.value = this._defaultValue ?? "";
  }
  _syncValidity() {
    const e = this.shadowRoot.querySelector("input");
    e.checkValidity() ? this._internals.setValidity({}) : this._internals.setValidity(e.validity, e.validationMessage, e);
  }
  _onInput(e) {
    this.value = e.target.value;
  }
  render() {
    return c`
      <input
        type="${this.type}"
        name="${this.name}"
        placeholder="${this.placeholder || d}"
        .value="${this.value}"
        ?required="${this.required}"
        pattern="${this.pattern || d}"
        autocomplete="${this.autocomplete || d}"
        ?disabled="${this.disabled}"
        ?readonly="${this.readonly}"
        class="input rounded-box w-full${this.error ? " input-error" : ""}"
        aria-invalid="${this.error ? "true" : d}"
        @input="${this._onInput}"
      />
    `;
  }
}
n(P, "formAssociated", !0), n(P, "styles", [
  b,
  h`
      :host {
        display: block;
      }
    `
]), n(P, "properties", {
  name: { type: String, reflect: !0 },
  type: { type: String, reflect: !0 },
  placeholder: { type: String },
  value: { type: String, reflect: !0 },
  required: { type: Boolean, reflect: !0 },
  pattern: { type: String, reflect: !0 },
  autocomplete: { type: String, reflect: !0 },
  disabled: { type: Boolean, reflect: !0 },
  readonly: { type: Boolean, reflect: !0 },
  error: { type: Boolean, reflect: !0 }
});
customElements.define("u-input", P);
class ae extends p {
  constructor() {
    super(), this.value = "", this.active = !1;
  }
  connectedCallback() {
    super.connectedCallback(), this.setAttribute("role", "option"), this.id || (this.id = `u-combobox-item-${Math.random().toString(36).slice(2)}`);
  }
  render() {
    return c`
      <div class="px-4 py-2 cursor-pointer ${this.active ? "bg-base-200" : ""}">
        <slot></slot>
      </div>
    `;
  }
}
n(ae, "styles", [
  b,
  h`
      :host {
        display: block;
      }
      :host(:focus-visible) {
        outline: 2px solid var(--color-primary);
        outline-offset: -2px;
        border-radius: var(--radius-btn);
      }
    `
]), n(ae, "properties", {
  value: { type: String, reflect: !0 },
  active: { type: Boolean, reflect: !0 }
});
customElements.define("u-combobox-item", ae);
class R extends p {
  constructor() {
    super(), this._internals = this.attachInternals(), this.name = "", this.label = "", this.placeholder = "", this.value = "", this.displayValue = "", this.required = !1, this.disabled = !1, this.error = !1, this.invalidMessage = "Please select a valid option.", this.requiredMessage = "Please select an option.", this._open = !1, this._activeIndex = -1, this._activeItemId = "", this._blurTimeout = null, this._suppressOpen = !1, this._suppressOpenTimeout = null, this._dropdownId = `u-combobox-dropdown-${Math.random().toString(36).slice(2)}`;
  }
  connectedCallback() {
    this._defaultValue === void 0 && (this._defaultValue = this.getAttribute("value") ?? "", this._defaultDisplayValue = this.getAttribute("display-value") ?? ""), super.connectedCallback(), this.addEventListener("click", this._onItemClick), this.addEventListener("invalid", this._onInvalid);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this.removeEventListener("click", this._onItemClick), this.removeEventListener("invalid", this._onInvalid), clearTimeout(this._blurTimeout), clearTimeout(this._suppressOpenTimeout);
  }
  firstUpdated() {
    var e;
    if (this.displayValue) {
      const t = (e = this.shadowRoot) == null ? void 0 : e.querySelector("input");
      t && (t.value = this.displayValue);
    }
    this._syncValidity();
  }
  updated(e) {
    e.has("value") && this._internals.setFormValue(this.value), (e.has("value") || e.has("required") || e.has("disabled")) && this._syncValidity();
  }
  formResetCallback() {
    var t;
    this.value = this._defaultValue ?? "";
    const e = (t = this.shadowRoot) == null ? void 0 : t.querySelector("input");
    e && (e.value = this._defaultDisplayValue ?? "");
  }
  _syncValidity() {
    var a;
    const e = (a = this.shadowRoot) == null ? void 0 : a.querySelector("input");
    if (!e) return;
    const t = this._getListItems(), o = t.length > 0, r = t.some((s) => s.getAttribute("value") === this.value);
    o && this.value && !r ? (this._internals.setValidity({ badInput: !0 }, this.invalidMessage, e), e.setAttribute("aria-invalid", "true")) : this.required && !this.value ? (this._internals.setValidity({ valueMissing: !0 }, this.requiredMessage, e), e.setAttribute("aria-invalid", "true")) : (this._internals.setValidity({}), e.removeAttribute("aria-invalid"));
  }
  _getListItems() {
    return [...this.querySelectorAll("u-combobox-item")];
  }
  _onFocus() {
    if (clearTimeout(this._blurTimeout), this._suppressOpen) {
      this._suppressOpen = !1;
      return;
    }
    this._open = !0;
  }
  _onInvalid() {
    this._open = !1, this._suppressOpen = !0, clearTimeout(this._suppressOpenTimeout), this._suppressOpenTimeout = setTimeout(() => {
      this._suppressOpen = !1;
    }, 0);
  }
  _onInputMouseDown() {
    this._open = !0;
  }
  _onBlur() {
    this._blurTimeout = setTimeout(() => {
      this._open = !1, this._setActiveIndex(-1);
    }, 150);
  }
  _onSearchInput(e) {
    this._open = !0, this.value = "", this.dispatchEvent(
      new CustomEvent("u-search", {
        detail: { query: e.target.value },
        bubbles: !0,
        composed: !0
      })
    );
  }
  _onKeyDown(e) {
    const t = this._getListItems();
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault(), this._open = !0, this._setActiveIndex(Math.min(this._activeIndex + 1, t.length - 1));
        break;
      case "ArrowUp":
        e.preventDefault(), this._setActiveIndex(Math.max(this._activeIndex - 1, 0));
        break;
      case "Enter":
        this._activeIndex >= 0 && t[this._activeIndex] && (e.preventDefault(), this._selectItem(t[this._activeIndex]));
        break;
      case "Escape":
        this._open = !1, this._setActiveIndex(-1);
        break;
    }
  }
  _onItemClick(e) {
    const t = e.composedPath().find((o) => o.tagName === "U-COMBOBOX-ITEM");
    t && this._selectItem(t);
  }
  _onDropdownMouseDown(e) {
    e.composedPath().some((t) => t.tagName === "U-COMBOBOX-ITEM") && e.preventDefault();
  }
  _selectItem(e) {
    var a;
    const t = e.getAttribute("value") ?? "", o = e.textContent.trim();
    this.value = t;
    const r = (a = this.shadowRoot) == null ? void 0 : a.querySelector("input");
    r && (r.value = o), this._open = !1, this._setActiveIndex(-1), this.dispatchEvent(
      new CustomEvent("u-change", {
        detail: { value: t, label: o },
        bubbles: !0,
        composed: !0
      })
    );
  }
  _setActiveIndex(e) {
    const t = this._getListItems();
    t.forEach((o, r) => {
      o.active = r === e, o.setAttribute("aria-selected", String(r === e));
    }), this._activeIndex = e, this._activeItemId = e >= 0 && t[e] ? t[e].id : "";
  }
  _onSlotChange() {
    this._setActiveIndex(-1), this._syncValidity();
  }
  render() {
    return c`
      <input
        type="text"
        role="combobox"
        autocomplete="off"
        aria-autocomplete="list"
        aria-haspopup="listbox"
        aria-expanded="${this._open}"
        aria-activedescendant="${this._activeItemId || d}"
        aria-controls="${this._dropdownId}"
        aria-label="${this.label || d}"
        placeholder="${this.placeholder || d}"
        class="input w-full${this.error ? " input-error" : ""}"
        ?disabled="${this.disabled}"
        @focus="${this._onFocus}"
        @blur="${this._onBlur}"
        @mousedown="${this._onInputMouseDown}"
        @input="${this._onSearchInput}"
        @keydown="${this._onKeyDown}"
      />
      <div
        id="${this._dropdownId}"
        class="dropdown-wrapper max-h-60 overflow-y-auto bg-base-100 border border-base-300 rounded-box shadow-sm"
        role="listbox"
        ?hidden="${!this._open}"
        @mousedown="${this._onDropdownMouseDown}"
      >
        <slot @slotchange="${this._onSlotChange}"></slot>
      </div>
    `;
  }
}
n(R, "formAssociated", !0), n(R, "styles", [
  b,
  h`
      :host {
        display: block;
        position: relative;
      }
      .dropdown-wrapper {
        position: absolute;
        top: 100%;
        left: 0;
        z-index: 10;
        width: 100%;
      }
    `
]), n(R, "properties", {
  name: { type: String, reflect: !0 },
  label: { type: String },
  placeholder: { type: String },
  value: { type: String, reflect: !0 },
  displayValue: { type: String, attribute: "display-value" },
  required: { type: Boolean, reflect: !0 },
  disabled: { type: Boolean, reflect: !0 },
  error: { type: Boolean, reflect: !0 },
  invalidMessage: { type: String, attribute: "invalid-message" },
  requiredMessage: { type: String, attribute: "required-message" },
  _open: { state: !0 },
  _activeIndex: { state: !0 },
  _activeItemId: { state: !0 }
});
customElements.define("u-combobox", R);
class se extends p {
  constructor() {
    super(), this.value = "", this.selected = !1, this.active = !1, this.disabled = !1;
  }
  connectedCallback() {
    super.connectedCallback(), this.setAttribute("role", "option"), this.id || (this.id = `u-multiselect-option-${Math.random().toString(36).slice(2)}`), this.setAttribute("aria-selected", String(this.selected)), this.disabled && this.setAttribute("aria-disabled", "true");
  }
  updated(e) {
    e.has("selected") && this.setAttribute("aria-selected", String(this.selected)), e.has("disabled") && (this.disabled ? this.setAttribute("aria-disabled", "true") : this.removeAttribute("aria-disabled"));
  }
  render() {
    return c`
      <div
        class="px-4 py-2 flex items-center gap-2 cursor-pointer ${this.active ? "bg-base-200" : ""}${this.disabled ? " opacity-50 cursor-not-allowed" : ""}"
      >
        <input
          type="checkbox"
          class="checkbox checkbox-sm pointer-events-none"
          tabindex="-1"
          aria-hidden="true"
          ?checked="${this.selected}"
          ?disabled="${this.disabled}"
        />
        <slot></slot>
      </div>
    `;
  }
}
n(se, "styles", [
  b,
  h`
      :host {
        display: block;
      }
      :host(:focus-visible) {
        outline: 2px solid var(--color-primary);
        outline-offset: -2px;
        border-radius: var(--radius-btn);
      }
    `
]), n(se, "properties", {
  value: { type: String, reflect: !0 },
  selected: { type: Boolean, reflect: !0 },
  active: { type: Boolean, reflect: !0 },
  disabled: { type: Boolean, reflect: !0 }
});
customElements.define("u-multiselect-option", se);
class H extends p {
  constructor() {
    super(), this._internals = this.attachInternals(), this.name = "", this.placeholder = "", this.disabled = !1, this.required = !1, this.error = !1, this.invalidMessage = "Please select at least one option.", this.requiredMessage = "Please select at least one option.", this._open = !1, this._activeIndex = -1, this._activeItemId = "", this._selections = [], this._liveMessage = "", this._lastQuery = "", this._blurTimeout = null, this._suppressOpen = !1, this._suppressOpenTimeout = null, this._dropdownId = `u-multiselect-dropdown-${Math.random().toString(36).slice(2)}`;
  }
  connectedCallback() {
    super.connectedCallback(), this.addEventListener("click", this._onOptionClick), this.addEventListener("invalid", this._onInvalid);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this.removeEventListener("click", this._onOptionClick), this.removeEventListener("invalid", this._onInvalid), clearTimeout(this._blurTimeout), clearTimeout(this._suppressOpenTimeout);
  }
  firstUpdated() {
    this._syncValidity(), this._refreshDisplay();
  }
  updated(e) {
    (e.has("required") || e.has("disabled")) && this._syncValidity(), e.has("_open") && !this._open && this._refreshDisplay();
  }
  formResetCallback() {
    this._selections = [], this._liveMessage = "", this._lastQuery = "", this._getOptions().forEach((e) => {
      e.selected = !1;
    }), this._syncFormValue(), this._refreshDisplay();
  }
  // The visible <input> is the search box while focused and the selection
  // summary while closed. This writes the summary; it is a no-op while the
  // dropdown is open so an in-progress search query is never clobbered.
  _refreshDisplay() {
    var t;
    if (this._open) return;
    const e = (t = this.shadowRoot) == null ? void 0 : t.querySelector("input");
    e && (e.value = this._summaryText());
  }
  _summaryText() {
    const e = this._selections.map((o) => o.label);
    if (e.length === 0) return "";
    const t = 2;
    return e.length <= t ? e.join(", ") : `${e.slice(0, t).join(", ")} +${e.length - t}`;
  }
  _getOptions() {
    return [...this.querySelectorAll("u-multiselect-option")];
  }
  _syncFormValue() {
    const e = new FormData();
    for (const { value: t } of this._selections)
      e.append(this.name, t);
    this._internals.setFormValue(e);
  }
  _syncValidity() {
    var t;
    const e = (t = this.shadowRoot) == null ? void 0 : t.querySelector("input");
    e && (this.required && this._selections.length === 0 ? (this._internals.setValidity({ valueMissing: !0 }, this.requiredMessage, e), e.setAttribute("aria-invalid", "true")) : (this._internals.setValidity({}), e.removeAttribute("aria-invalid")));
  }
  _toggleOption(e) {
    if (e.disabled) return;
    const t = e.value, o = e.textContent.trim(), r = this._selections.findIndex((a) => a.value === t);
    r >= 0 ? (this._selections = this._selections.filter((a, s) => s !== r), e.selected = !1, this._liveMessage = `${o} removed, ${this._selections.length} selected`) : (this._selections = [...this._selections, { value: t, label: o }], e.selected = !0, this._liveMessage = `${o} added, ${this._selections.length} selected`), this._syncFormValue(), this._syncValidity(), this._refreshDisplay(), this.dispatchEvent(
      new CustomEvent("u-change", {
        detail: { values: this._selections.map((a) => a.value) },
        bubbles: !0,
        composed: !0
      })
    );
  }
  _setActiveIndex(e) {
    const t = this._getOptions();
    t.forEach((o, r) => {
      o.active = r === e;
    }), this._activeIndex = e, this._activeItemId = e >= 0 && t[e] ? t[e].id : "";
  }
  _onFocus() {
    var t;
    clearTimeout(this._blurTimeout);
    const e = (t = this.shadowRoot) == null ? void 0 : t.querySelector("input");
    if (e && (e.value = this._lastQuery), this._suppressOpen) {
      this._suppressOpen = !1;
      return;
    }
    this._open = !0;
  }
  _onInvalid() {
    this._open = !1, this._suppressOpen = !0, clearTimeout(this._suppressOpenTimeout), this._suppressOpenTimeout = setTimeout(() => {
      this._suppressOpen = !1;
    }, 0);
  }
  _onInputMouseDown() {
    this._open = !0;
  }
  _onBlur() {
    this._blurTimeout = setTimeout(() => {
      this._open = !1, this._setActiveIndex(-1);
    }, 150);
  }
  _onSearchInput(e) {
    this._open = !0, this._lastQuery = e.target.value, this.dispatchEvent(
      new CustomEvent("u-search", {
        detail: { query: e.target.value },
        bubbles: !0,
        composed: !0
      })
    );
  }
  _onOptionClick(e) {
    const t = e.composedPath().find((o) => o.tagName === "U-MULTISELECT-OPTION");
    t && (clearTimeout(this._blurTimeout), this._toggleOption(t));
  }
  _onDropdownMouseDown(e) {
    e.composedPath().some((t) => t.tagName === "U-MULTISELECT-OPTION") && e.preventDefault();
  }
  _onKeyDown(e) {
    var o;
    const t = this._getOptions();
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault(), this._open = !0, this._setActiveIndex(Math.min(this._activeIndex + 1, t.length - 1));
        break;
      case "ArrowUp":
        e.preventDefault(), this._setActiveIndex(Math.max(this._activeIndex - 1, 0));
        break;
      case "Enter":
      case " ":
        this._activeIndex >= 0 && t[this._activeIndex] && (e.preventDefault(), this._toggleOption(t[this._activeIndex]));
        break;
      case "Escape":
        this._open = !1, this._setActiveIndex(-1);
        break;
      case "Backspace": {
        const r = (o = this.shadowRoot) == null ? void 0 : o.querySelector("input");
        if (r && r.value === "" && this._selections.length > 0) {
          const a = this._selections[this._selections.length - 1], s = this._getOptions().find((u) => u.value === a.value);
          s ? this._toggleOption(s) : (this._selections = this._selections.slice(0, -1), this._liveMessage = `${a.label} removed, ${this._selections.length} selected`, this._syncFormValue(), this._syncValidity(), this._refreshDisplay());
        }
        break;
      }
    }
  }
  _onSlotChange() {
    this._setActiveIndex(-1);
    for (const e of this._getOptions())
      this._selections.some((t) => t.value === e.value) ? e.selected = !0 : e.selected && (this._selections = [
        ...this._selections,
        { value: e.value, label: e.textContent.trim() }
      ]);
    this._syncFormValue(), this._syncValidity(), this._refreshDisplay();
  }
  render() {
    return c`
      <input
        type="text"
        role="combobox"
        autocomplete="off"
        aria-autocomplete="list"
        aria-haspopup="listbox"
        aria-expanded="${this._open}"
        aria-activedescendant="${this._activeItemId || d}"
        aria-controls="${this._dropdownId}"
        placeholder="${this.placeholder || d}"
        class="input w-full${this.error ? " input-error" : ""}"
        ?disabled="${this.disabled}"
        @focus="${this._onFocus}"
        @blur="${this._onBlur}"
        @mousedown="${this._onInputMouseDown}"
        @input="${this._onSearchInput}"
        @keydown="${this._onKeyDown}"
      />
      <div
        id="${this._dropdownId}"
        class="dropdown-wrapper max-h-60 overflow-y-auto bg-base-100 border border-base-300 rounded-box shadow-sm"
        role="listbox"
        aria-multiselectable="true"
        ?hidden="${!this._open}"
        @mousedown="${this._onDropdownMouseDown}"
      >
        <slot @slotchange="${this._onSlotChange}"></slot>
      </div>
      <span class="sr-only" role="status" aria-live="polite">${this._liveMessage}</span>
    `;
  }
}
n(H, "formAssociated", !0), n(H, "styles", [
  b,
  h`
      :host {
        display: block;
        position: relative;
      }
      .dropdown-wrapper {
        position: absolute;
        top: 100%;
        left: 0;
        z-index: 10;
        width: 100%;
      }
    `
]), n(H, "properties", {
  name: { type: String, reflect: !0 },
  placeholder: { type: String },
  disabled: { type: Boolean, reflect: !0 },
  required: { type: Boolean, reflect: !0 },
  error: { type: Boolean, reflect: !0 },
  invalidMessage: { type: String, attribute: "invalid-message" },
  requiredMessage: { type: String, attribute: "required-message" },
  _open: { state: !0 },
  _activeIndex: { state: !0 },
  _activeItemId: { state: !0 },
  _selections: { state: !0 },
  _liveMessage: { state: !0 }
});
customElements.define("u-multiselect", H);
class ne extends p {
  constructor() {
    super(), this.value = "", this.selected = !1, this.active = !1, this.disabled = !1, this.accent = "none", this._hasSublabel = !1;
  }
  connectedCallback() {
    super.connectedCallback(), this.setAttribute("role", "option"), this.id || (this.id = `u-list-select-item-${Math.random().toString(36).slice(2)}`), this.setAttribute("aria-selected", String(this.selected)), this.disabled && this.setAttribute("aria-disabled", "true");
  }
  updated(e) {
    e.has("selected") && this.setAttribute("aria-selected", String(this.selected)), e.has("disabled") && (this.disabled ? this.setAttribute("aria-disabled", "true") : this.removeAttribute("aria-disabled"));
  }
  /**
   * The item's label text — the default slot only. `textContent` would also pick
   * up the sublabel and any trailing action, so the parent uses this instead when
   * building `u-change`'s `detail.label`.
   * @type {string}
   */
  get label() {
    var t;
    const e = (t = this.shadowRoot) == null ? void 0 : t.querySelector("slot:not([name])");
    return e ? e.assignedNodes({ flatten: !0 }).map((o) => o.textContent).join("").trim() : this.textContent.trim();
  }
  _onSublabelSlotChange(e) {
    this._hasSublabel = e.target.assignedNodes({ flatten: !0 }).length > 0;
  }
  get _classes() {
    const e = ["flex items-stretch gap-3 px-3 py-2 cursor-pointer"];
    return (this.selected || this.active) && e.push("border-l-2 border-primary"), e.push(this.selected ? "bg-primary/10 font-semibold" : "hover:bg-base-200"), this.disabled && e.push("opacity-50 cursor-not-allowed"), e.join(" ");
  }
  render() {
    return c`
      <div class="${this._classes}">
        <span class="bar" aria-hidden="true"></span>
        <div class="flex-1 min-w-0 self-center">
          <div class="truncate text-base"><slot></slot></div>
          <div class="truncate text-xs opacity-60" ?hidden="${!this._hasSublabel}">
            <slot name="sublabel" @slotchange="${this._onSublabelSlotChange}"></slot>
          </div>
        </div>
        <div class="self-center"><slot name="action"></slot></div>
      </div>
    `;
  }
}
n(ne, "styles", [
  b,
  h`
      :host {
        display: block;
      }
      :host(:focus-visible) {
        outline: 2px solid var(--color-primary);
        outline-offset: -2px;
        border-radius: var(--radius-btn);
      }
      /* One static rule per accent value: a runtime-composed class name would be
         invisible to Tailwind's static extraction and emit no CSS at all. */
      .bar {
        width: 3px;
        flex: none;
        border-radius: 2px;
        background: transparent;
      }
      :host([accent='primary']) .bar {
        background: var(--color-primary);
      }
      :host([accent='secondary']) .bar {
        background: var(--color-secondary);
      }
      :host([accent='accent']) .bar {
        background: var(--color-accent);
      }
      :host([accent='info']) .bar {
        background: var(--color-info);
      }
      :host([accent='success']) .bar {
        background: var(--color-success);
      }
      :host([accent='warning']) .bar {
        background: var(--color-warning);
      }
      :host([accent='error']) .bar {
        background: var(--color-error);
      }
    `
]), n(ne, "properties", {
  value: { type: String, reflect: !0 },
  selected: { type: Boolean, reflect: !0 },
  active: { type: Boolean, reflect: !0 },
  disabled: { type: Boolean, reflect: !0 },
  accent: { type: String, reflect: !0 },
  _hasSublabel: { state: !0 }
});
customElements.define("u-list-select-item", ne);
class le extends p {
  constructor() {
    super(), this.heading = "", this.sticky = !1;
  }
  connectedCallback() {
    super.connectedCallback(), this.setAttribute("role", "group"), this.heading && this.setAttribute("aria-label", this.heading);
  }
  updated(e) {
    e.has("heading") && (this.heading ? this.setAttribute("aria-label", this.heading) : this.removeAttribute("aria-label"));
  }
  render() {
    return c`
      <div
        class="heading px-3 pt-2 pb-1 text-xs font-semibold uppercase tracking-wide bg-base-100"
        aria-hidden="true"
      >
        ${this.heading}
      </div>
      <slot></slot>
    `;
  }
}
n(le, "styles", [
  b,
  h`
      :host {
        display: block;
      }
      :host([sticky]) .heading {
        position: sticky;
        top: 0;
        z-index: 1;
      }
    `
]), n(le, "properties", {
  heading: { type: String },
  sticky: { type: Boolean, reflect: !0 }
});
customElements.define("u-list-select-group", le);
class L extends p {
  constructor() {
    super(), this._internals = this.attachInternals(), this.name = "", this.value = "", this.heading = "", this.label = "", this.count = null, this.placeholder = "", this.filterable = !1, this.size = "md", this.grow = !1, this.required = !1, this.disabled = !1, this.error = !1, this.requiredMessage = "Please select an option.", this._activeIndex = -1, this._activeItemId = "", this._itemCount = 0, this._hasSelection = !1;
    const e = Math.random().toString(36).slice(2);
    this._listId = `u-list-select-list-${e}`, this._headingId = `u-list-select-heading-${e}`;
  }
  connectedCallback() {
    this._defaultValue === void 0 && (this._defaultValue = this.getAttribute("value") ?? ""), super.connectedCallback(), this.addEventListener("click", this._onItemClick);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this.removeEventListener("click", this._onItemClick);
  }
  firstUpdated() {
    this._syncValidity();
  }
  willUpdate(e) {
    if (!this.hasUpdated) {
      this._readInitialSelection();
      return;
    }
    e.has("value") && !e.has("_hasSelection") && (this._hasSelection = this.value !== "");
  }
  // Runs in willUpdate rather than firstUpdated: this seeds reactive state, and
  // doing that from firstUpdated would schedule a second update. It also has to
  // land before the first _applySelection, which would otherwise clear an
  // attribute-set `selected` before anything could read it.
  _readInitialSelection() {
    const e = this._getItems();
    if (this._itemCount = e.length, this._hasSelection = this.value !== "", this._hasSelection) return;
    const t = e.find((o) => o.hasAttribute("selected"));
    t && (this.value = t.getAttribute("value") ?? "", this._hasSelection = !0);
  }
  updated(e) {
    (e.has("value") || e.has("_hasSelection")) && (this._internals.setFormValue(this.value), this._applySelection()), (e.has("value") || e.has("_hasSelection") || e.has("required") || e.has("disabled")) && this._syncValidity();
  }
  formResetCallback() {
    this.value = this._defaultValue ?? "", this._hasSelection = this.value !== "";
    const e = this._filterInput;
    e && (e.value = "");
  }
  get _filterInput() {
    var e;
    return (e = this.shadowRoot) == null ? void 0 : e.querySelector("input");
  }
  get _listbox() {
    var e;
    return (e = this.shadowRoot) == null ? void 0 : e.querySelector('[role="listbox"]');
  }
  _getItems() {
    return [...this.querySelectorAll("u-list-select-item")];
  }
  _applySelection() {
    const e = this._getItems(), t = this._hasSelection ? e.find((o) => o.value === this.value) : void 0;
    for (const o of e)
      o.selected = o === t;
  }
  _syncValidity() {
    const e = this._filterInput ?? this._listbox;
    e && (this.required && !this._hasSelection ? (this._internals.setValidity({ valueMissing: !0 }, this.requiredMessage, e), e.setAttribute("aria-invalid", "true")) : (this._internals.setValidity({}), e.removeAttribute("aria-invalid")));
  }
  _selectItem(e) {
    var t;
    this.disabled || e.disabled || (this.value = e.value, this._hasSelection = !0, this._setActiveIndex(this._getItems().indexOf(e)), (t = this._filterInput ?? this._listbox) == null || t.focus(), this.dispatchEvent(
      new CustomEvent("u-change", {
        detail: { value: e.value, label: e.label },
        bubbles: !0,
        composed: !0
      })
    ));
  }
  _onItemClick(e) {
    const t = e.composedPath();
    if (t.some((r) => {
      var a;
      return ((a = r == null ? void 0 : r.getAttribute) == null ? void 0 : a.call(r, "slot")) === "action";
    })) return;
    const o = t.find((r) => r.tagName === "U-LIST-SELECT-ITEM");
    o && this._selectItem(o);
  }
  _setActiveIndex(e) {
    var o;
    const t = this._getItems();
    t.forEach((r, a) => {
      r.active = a === e;
    }), this._activeIndex = e, this._activeItemId = e >= 0 && t[e] ? t[e].id : "", (o = t[e]) == null || o.scrollIntoView({ block: "nearest" });
  }
  _moveActive(e) {
    const t = this._getItems();
    let o = this._activeIndex;
    for (let r = 0; r < t.length; r++) {
      if (o += e, o < 0 || o >= t.length) return;
      if (!t[o].disabled) {
        this._setActiveIndex(o);
        return;
      }
    }
  }
  _moveEdge(e) {
    const t = this._getItems(), o = t.map((r, a) => a);
    e === "last" && o.reverse();
    for (const r of o)
      if (!t[r].disabled) {
        this._setActiveIndex(r);
        return;
      }
  }
  _clearFilter() {
    const e = this._filterInput;
    !e || e.value === "" || (e.value = "", this.dispatchEvent(
      new CustomEvent("u-search", { detail: { query: "" }, bubbles: !0, composed: !0 })
    ));
  }
  _onKeyDown(e) {
    if (e.composedPath().some((o) => {
      var r;
      return ((r = o == null ? void 0 : o.getAttribute) == null ? void 0 : r.call(o, "slot")) === "action";
    })) return;
    const t = this._getItems();
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault(), this._activeIndex < 0 ? this._moveEdge("first") : this._moveActive(1);
        break;
      case "ArrowUp":
        e.preventDefault(), this._activeIndex < 0 ? this._moveEdge("first") : this._moveActive(-1);
        break;
      case "Home":
        e.preventDefault(), this._moveEdge("first");
        break;
      case "End":
        e.preventDefault(), this._moveEdge("last");
        break;
      case " ":
        if (this.filterable) break;
        this._activeIndex >= 0 && t[this._activeIndex] && (e.preventDefault(), this._selectItem(t[this._activeIndex]));
        break;
      case "Enter":
        this._activeIndex >= 0 && t[this._activeIndex] && (e.preventDefault(), this._selectItem(t[this._activeIndex]));
        break;
      case "Escape":
        this._clearFilter();
        break;
    }
  }
  _onSearchInput(e) {
    this.dispatchEvent(
      new CustomEvent("u-search", {
        detail: { query: e.target.value },
        bubbles: !0,
        composed: !0
      })
    );
  }
  _onSlotChange() {
    const e = this._getItems();
    if (this._itemCount = e.length, !this._hasSelection) {
      const t = e.find((o) => o.selected);
      t && (this.value = t.value, this._hasSelection = !0);
    }
    this._applySelection(), this._setActiveIndex(-1), this._syncValidity();
  }
  _renderHeading() {
    if (!this.heading) return d;
    const e = this.count ?? this._itemCount;
    return c`
      <div class="flex items-center gap-1 ml-2 mb-1">
        <span id="${this._headingId}" class="text-base font-semibold truncate">
          ${this.heading}
        </span>
        <span class="text-sm opacity-60 whitespace-nowrap">· ${e}</span>
        <span class="flex-1"></span>
        <slot name="header-action"></slot>
      </div>
    `;
  }
  render() {
    return c`
      ${this._renderHeading()}
      ${this.filterable ? c`
            <input
              type="text"
              role="combobox"
              autocomplete="off"
              aria-autocomplete="list"
              aria-haspopup="listbox"
              aria-expanded="true"
              aria-controls="${this._listId}"
              aria-activedescendant="${this._activeItemId || d}"
              aria-label="${this.heading || this.label || d}"
              placeholder="${this.placeholder || d}"
              class="input input-md w-full rounded-box mb-1${this.error ? " input-error" : ""}"
              ?disabled="${this.disabled}"
              @input="${this._onSearchInput}"
              @keydown="${this._onKeyDown}"
            />
          ` : d}
      <div
        id="${this._listId}"
        class="list overflow-y-auto bg-base-100 border border-base-300 rounded-box"
        role="listbox"
        aria-labelledby="${this.heading ? this._headingId : d}"
        aria-label="${!this.heading && this.label ? this.label : d}"
        aria-activedescendant="${!this.filterable && this._activeItemId ? this._activeItemId : d}"
        tabindex="${this.filterable ? d : "0"}"
        @keydown="${this._onKeyDown}"
      >
        <slot @slotchange="${this._onSlotChange}"></slot>
        <div class="px-4 py-8 text-center text-sm opacity-60" ?hidden="${this._itemCount > 0}">
          <slot name="empty"></slot>
        </div>
      </div>
    `;
  }
}
n(L, "formAssociated", !0), n(L, "styles", [
  b,
  h`
      :host {
        display: block;
        /* Heights live here rather than in interpolated utility classes:
           Tailwind extracts class names statically, so a class built at
           runtime emits no CSS. --u-md-height is local to this component —
           auto's cap is defined as "the md height", not a second literal
           that has to be kept equal to it by hand. */
        --u-md-height: calc(var(--spacing) * 80);
      }
      .list {
        height: var(--u-md-height);
      }
      :host([size='sm']) .list {
        height: calc(var(--spacing) * 50);
      }
      :host([size='lg']) .list {
        height: calc(var(--spacing) * 120);
      }
      /* Hugs the option count instead of forcing the full md height — only
         scrolls once the list actually grows past that cap. */
      :host([size='auto']) .list {
        height: auto;
        max-height: var(--u-md-height);
      }
      :host([grow]) {
        display: flex;
        flex-direction: column;
        flex: 1 1 0;
        min-height: 0;
      }
      :host([grow]) .list {
        height: auto;
        flex: 1 1 0;
        min-height: 0;
      }
      :host([error]) .list {
        border-color: var(--color-error);
      }
    `
]), n(L, "properties", {
  name: { type: String, reflect: !0 },
  value: { type: String, reflect: !0 },
  heading: { type: String },
  label: { type: String },
  count: { type: Number },
  placeholder: { type: String },
  filterable: { type: Boolean, reflect: !0 },
  size: { type: String, reflect: !0 },
  grow: { type: Boolean, reflect: !0 },
  required: { type: Boolean, reflect: !0 },
  disabled: { type: Boolean, reflect: !0 },
  error: { type: Boolean, reflect: !0 },
  requiredMessage: { type: String, attribute: "required-message" },
  _activeIndex: { state: !0 },
  _activeItemId: { state: !0 },
  _itemCount: { state: !0 },
  _hasSelection: { state: !0 }
});
customElements.define("u-list-select", L);
class ce extends p {
  constructor() {
    super(), this.variant = "ghost", this.size = "sm", this.dot = !1;
  }
  get _classes() {
    const e = ["badge", `badge-${this.variant}`];
    return this.dot ? e.push("badge-xs") : (this.size === "sm" && e.push("badge-sm"), this.size === "lg" && e.push("badge-lg")), e.join(" ");
  }
  updated() {
    this.dot ? this.setAttribute("aria-label", this.textContent.trim()) : this.removeAttribute("aria-label");
  }
  render() {
    return c`<span class="${this._classes}">${this.dot ? "" : c`<slot></slot>`}</span>`;
  }
}
n(ce, "styles", [
  b,
  h`
      :host {
        display: inline-block;
      }
    `
]), n(ce, "properties", {
  variant: { type: String, reflect: !0 },
  size: { type: String, reflect: !0 },
  dot: { type: Boolean, reflect: !0 }
});
customElements.define("u-badge", ce);
class de extends p {
  constructor() {
    super(), this.empty = !1, this.stickyHeader = !1;
  }
  connectedCallback() {
    super.connectedCallback(), this.setAttribute("role", "table");
  }
  render() {
    return c`
      <div class="${this.stickyHeader ? "w-full" : "overflow-x-auto w-full"}">
        <div class="table w-full text-sm">
          <div class="table-header-group">
            <slot name="header"></slot>
          </div>
          ${this.empty ? c`
                <div class="table-row">
                  <div class="table-cell text-center py-4">
                    <slot name="empty"></slot>
                  </div>
                </div>
              ` : c`<slot></slot>`}
          <div class="table-footer-group">
            <slot name="footer"></slot>
          </div>
        </div>
      </div>
    `;
  }
}
n(de, "properties", {
  empty: { type: Boolean, reflect: !0 },
  stickyHeader: { type: Boolean, reflect: !0, attribute: "sticky-header" },
  striped: { type: Boolean, reflect: !0 }
}), n(de, "styles", [
  b,
  h`
      :host {
        display: block;
      }
      /* An overflow container on either axis computes the other axis to auto,
         which would make the inner wrapper a vertical scroll container and trap
         the sticky header at the top of the (un-scrolling) full table. When
         sticky, defer both axes to the ancestor scroll region instead. */
      :host([sticky-header]) .table-header-group {
        position: sticky;
        top: 0;
        z-index: 1;
        background-color: var(--color-base-100);
      }
      /* Forwarded through inheritance into the header row's slotted cells
         (custom properties pierce shadow boundaries), so only its outer two
         cells round themselves to the table's own top corners — see
         u-tbody for the matching bottom-corner forwarding. */
      ::slotted([slot='header']) {
        --u-row-top-radius: var(--radius-box);
      }
      /* Forwarded into every body row (custom properties pierce shadow
         boundaries); u-tr applies it only to its even rows. Unset (and thus
         u-tr's own fallback to the plain surface color) unless striped. */
      :host([striped]) ::slotted(u-tbody) {
        --u-row-stripe: color-mix(in srgb, var(--color-base-100) 97%, var(--color-base-content));
      }
    `
]);
customElements.define("u-table", de);
class Fe extends p {
  connectedCallback() {
    super.connectedCallback(), this.setAttribute("role", "rowgroup");
  }
  render() {
    return c`<slot></slot>`;
  }
}
n(Fe, "styles", [
  b,
  h`
      :host {
        display: table-row-group;
      }
      /* Forwarded through inheritance into the row's slotted cells (custom
         properties pierce shadow boundaries), so only the table's bottom
         corner cells round themselves — otherwise the hover/selected
         highlight on the last row exposes a square corner past the table's
         own rounded container. The top corners belong to the header row
         (u-table), not the body's first row. */
      ::slotted(u-tr:last-child) {
        --u-row-bottom-radius: var(--radius-box);
      }
    `
]);
customElements.define("u-tbody", Fe);
class pe extends p {
  constructor() {
    super(), this.selected = !1;
  }
  connectedCallback() {
    super.connectedCallback(), this.setAttribute("role", "row"), this.selected && this.setAttribute("aria-selected", "true");
  }
  updated(e) {
    e.has("selected") && (this.selected ? this.setAttribute("aria-selected", "true") : this.removeAttribute("aria-selected"));
  }
  render() {
    return c`<slot></slot>`;
  }
}
n(pe, "styles", [
  b,
  h`
      :host {
        display: table-row;
        --u-cell-bg: var(--color-base-100);
      }
      /* --u-row-stripe comes from u-table's striped attribute; unset (and so
         falling back to the plain surface color) otherwise. */
      :host(:nth-child(even)) {
        --u-cell-bg: var(--u-row-stripe, var(--color-base-100));
      }
      :host(:hover) {
        --u-cell-bg: var(--color-base-200);
      }
      /* Selection gets a faded primary tint rather than the hover gray, so a
         selected row stays visually distinct once the pointer moves away.
         srgb, not oklch: --color-base-100 is oklch(100% 0 0) — chroma 0 with
         an explicit (not "none") hue of 0 — so oklch interpolation drags the
         mix towards that literal red-ish hue, tinting the result pink instead
         of green. Plain channel blending in srgb has no hue to skew. */
      :host([selected]) {
        --u-cell-bg: color-mix(
          in srgb,
          var(--color-primary) var(--u-tint-weak, 12%),
          var(--color-base-100)
        );
      }
    `
]), n(pe, "properties", {
  selected: { type: Boolean, reflect: !0 }
});
customElements.define("u-tr", pe);
const We = h`
  :host(:first-child) {
    border-top-left-radius: var(--u-row-top-radius, 0);
    border-bottom-left-radius: var(--u-row-bottom-radius, 0);
  }
  :host(:last-child) {
    border-top-right-radius: var(--u-row-top-radius, 0);
    border-bottom-right-radius: var(--u-row-bottom-radius, 0);
  }
`;
class ue extends p {
  constructor() {
    super(), this.direction = "none", this.sortable = !1;
  }
  connectedCallback() {
    super.connectedCallback(), this.setAttribute("role", "columnheader");
  }
  get _ariaLabel() {
    const e = this.textContent.trim();
    return this.direction === "asc" ? `${e}, sorted ascending` : this.direction === "desc" ? `${e}, sorted descending` : `${e}, sortable`;
  }
  updated(e) {
    if (e.has("direction")) {
      const t = { asc: "ascending", desc: "descending" };
      t[this.direction] ? this.setAttribute("aria-sort", t[this.direction]) : this.removeAttribute("aria-sort");
    }
    this.sortable ? this.setAttribute("aria-label", this._ariaLabel) : this.removeAttribute("aria-label");
  }
  render() {
    const e = this.sortable || this.direction !== "none", t = this.direction === "asc" ? "↑" : this.direction === "desc" ? "↓" : "↕";
    return c`
      <div
        class="px-4 py-3 text-xs font-semibold uppercase tracking-wide whitespace-nowrap flex items-center gap-1"
      >
        <slot></slot>
        ${e ? c`<span class="${this.direction === "none" ? "opacity-50" : ""}" aria-hidden="true"
              >${t}</span
            >` : d}
      </div>
    `;
  }
}
n(ue, "styles", [
  b,
  h`
      :host {
        display: table-cell;
        vertical-align: middle;
        background-color: var(--u-cell-bg, var(--color-base-100));
        border-bottom: 2px solid var(--color-base-300) !important;
      }
    `,
  We
]), n(ue, "properties", {
  direction: { type: String, reflect: !0 },
  sortable: { type: Boolean, reflect: !0 }
});
customElements.define("u-th", ue);
class Ke extends p {
  connectedCallback() {
    super.connectedCallback(), this.setAttribute("role", "cell");
  }
  render() {
    return c`<div class="px-4 py-3"><slot></slot></div>`;
  }
}
n(Ke, "styles", [
  b,
  h`
      :host {
        display: table-cell;
        vertical-align: middle;
        background-color: var(--u-cell-bg, var(--color-base-100));
      }
    `,
  We
]);
customElements.define("u-td", Ke);
class Ze extends p {
  render() {
    return c`<div class="w-full"><slot></slot></div>`;
  }
}
n(Ze, "styles", [
  b,
  h`
      :host {
        display: block;
      }
    `
]);
customElements.define("u-description-list", Ze);
class he extends p {
  constructor() {
    super(), this.label = "";
  }
  render() {
    return c`
      <div class="item-row flex gap-4 py-2 border-b">
        <span class="item-label shrink-0 font-medium" role="term">${this.label}</span>
        <span class="flex-1 min-w-0" role="definition"><slot></slot></span>
      </div>
    `;
  }
}
n(he, "styles", [
  b,
  h`
      :host {
        display: block;
      }
      .item-row {
        border-color: var(--u-description-item-divider, var(--color-base-200));
        border-style: var(--u-description-item-divider-style, solid);
      }
      .item-label {
        width: var(--u-description-item-label-width, 12rem);
        opacity: var(--u-description-item-label-opacity, 0.6);
      }
    `
]), n(he, "properties", {
  label: { type: String }
});
customElements.define("u-description-item", he);
class be extends p {
  constructor() {
    super(), this._theme = "univention-light", this.labelLight = "Switch to light theme", this.labelDark = "Switch to dark theme";
  }
  connectedCallback() {
    super.connectedCallback();
    const e = localStorage.getItem("theme");
    e === "univention-light" || e === "univention-dark" ? this._theme = e : window.matchMedia("(prefers-color-scheme: dark)").matches && (this._theme = "univention-dark"), this._applyTheme();
  }
  _applyTheme() {
    document.documentElement.dataset.theme = this._theme;
  }
  _toggle() {
    this._theme = this._theme === "univention-light" ? "univention-dark" : "univention-light", localStorage.setItem("theme", this._theme), this._applyTheme();
  }
  render() {
    const e = this._theme === "univention-dark";
    return c`
      <button
        type="button"
        class="btn btn-circle"
        role="switch"
        aria-checked="${e ? "true" : "false"}"
        @click="${this._toggle}"
        aria-label="${e ? this.labelLight : this.labelDark}"
      >
        ${e ? c`
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
                aria-hidden="true"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z"
                />
              </svg>
            ` : c`
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
                aria-hidden="true"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M21.752 15.002A9.72 9.72 0 0 1 18 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 0 0 3 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 0 0 9.002-5.998Z"
                />
              </svg>
            `}
      </button>
    `;
  }
}
n(be, "styles", [
  b,
  h`
      :host {
        display: inline-block;
      }
      :host button {
        background-color: var(--color-base-100);
        color: var(--color-base-content);
      }
    `
]), n(be, "properties", {
  _theme: { state: !0 },
  labelLight: { type: String, attribute: "label-light" },
  labelDark: { type: String, attribute: "label-dark" }
});
customElements.define("u-theme-toggle", be);
class me extends p {
  constructor() {
    super(), this.href = "", this.variant = "primary";
  }
  get _safeHref() {
    const e = this.href ?? "";
    return /^javascript:/i.test(e) ? "#" : e;
  }
  render() {
    return c`<a href="${this._safeHref}" class="link link-${this.variant}"><slot></slot></a>`;
  }
}
n(me, "styles", [
  b,
  h`
      :host {
        display: inline;
      }
    `
]), n(me, "properties", {
  href: { type: String },
  variant: { type: String, reflect: !0 }
});
customElements.define("u-link", me);
class ve extends p {
  constructor() {
    super(), this.level = "strong";
  }
  get _classes() {
    return this.level === "subtle" ? "italic" : this.level === "critical" ? "font-bold text-primary" : "font-semibold";
  }
  render() {
    return c`<strong class="${this._classes}"><slot></slot></strong>`;
  }
}
n(ve, "styles", [
  b,
  h`
      :host {
        display: inline;
      }
    `
]), n(ve, "properties", {
  level: { type: String, reflect: !0 }
});
customElements.define("u-emphasize", ve);
class fe extends p {
  constructor() {
    super(), this.visible = !1, this.inert = !0, this._firstMeasureDone = !1, this._resizeObserver = new ResizeObserver(() => this._measure());
  }
  updated(e) {
    e.has("visible") && (this.inert = !this.visible);
  }
  connectedCallback() {
    super.connectedCallback(), this.style.transition = "none";
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._resizeObserver.disconnect();
  }
  _measure() {
    this.style.setProperty("--u-collapsible-content-height", `${this.scrollHeight}px`);
  }
  // Slotted elements are re-observed on every slotchange rather than once,
  // since the assigned nodes themselves can be swapped out (not just resized)
  // — text nodes among them aren't observable, only Elements are.
  _onSlotChange(e) {
    this._resizeObserver.disconnect();
    for (const t of e.target.assignedElements({ flatten: !0 }))
      this._resizeObserver.observe(t);
    this._measure(), this._firstMeasureDone || (this._firstMeasureDone = !0, requestAnimationFrame(() => {
      this.style.transition = "";
    }));
  }
  render() {
    return c`<slot @slotchange="${this._onSlotChange}"></slot>`;
  }
}
n(fe, "styles", [
  b,
  h`
      :host {
        display: block;
        overflow: hidden;
        max-height: 0;
        opacity: 0;
        transition:
          max-height var(--u-collapsible-duration, 200ms) ease,
          opacity var(--u-collapsible-duration, 200ms) ease;
      }
      /* The measured height, not an arbitrary large cap: transitioning to a
         cap far bigger than the real content (the usual max-height trick)
         makes the animation finish visually well before the transition's
         nominal duration elapses, and that mismatch gets worse the smaller
         the content is relative to the cap. */
      :host([visible]) {
        max-height: var(--u-collapsible-content-height, 0px);
        opacity: 1;
      }
    `
]), n(fe, "properties", {
  visible: { type: Boolean, reflect: !0 }
});
customElements.define("u-collapsible", fe);
class ge extends p {
  constructor() {
    super(), this.variant = "", this.dismissible = !1, this.duration = 0, this._timeout = null;
  }
  connectedCallback() {
    super.connectedCallback(), this.duration > 0 && (this._timeout = setTimeout(() => this._dismiss(), this.duration));
  }
  disconnectedCallback() {
    super.disconnectedCallback(), clearTimeout(this._timeout);
  }
  _dismiss() {
    this.isConnected && (clearTimeout(this._timeout), this.dispatchEvent(new CustomEvent("u-close", { bubbles: !0, composed: !0 })), this.remove());
  }
  render() {
    return c`
      <div
        role="alert"
        class="alert${this.variant ? ` alert-${this.variant}` : ""} flex items-center gap-3"
      >
        <span class="flex-1"><slot></slot></span>
        ${this.dismissible ? c`
              <button
                type="button"
                class="u-dismiss-btn btn btn-ghost btn-sm btn-square shrink-0 rounded-box"
                aria-label="Dismiss"
                @click="${this._dismiss}"
              >
                ✕
              </button>
            ` : d}
      </div>
    `;
  }
}
n(ge, "styles", [
  b,
  h`
      :host {
        display: block;
      }
      /* DaisyUI's alert-{variant} class tints its text to match the variant
         (e.g. dark red on the error background); pin it back to the theme's
         normal text color so slotted content doesn't need to override this
         itself, and the dismiss button (which does its own color: below)
         doesn't visually clash with the message next to it. */
      .alert {
        color: var(--color-base-content);
      }
    `
]), n(ge, "properties", {
  variant: { type: String, reflect: !0 },
  dismissible: { type: Boolean, reflect: !0 },
  duration: { type: Number, reflect: !0 }
});
customElements.define("u-toast-item", ge);
class we extends p {
  constructor() {
    super(), this.position = "bottom-end";
  }
  get _classes() {
    const [e, t] = (this.position || "bottom-end").split("-"), o = ["toast"];
    return e === "top" && o.push("toast-top"), t === "start" && o.push("toast-start"), t === "center" && o.push("toast-center"), o.join(" ");
  }
  render() {
    return c`<div class="${this._classes}"><slot></slot></div>`;
  }
}
n(we, "styles", [
  b,
  h`
      :host {
        display: contents;
      }
    `
]), n(we, "properties", {
  position: { type: String, reflect: !0 }
});
customElements.define("u-toast", we);
if (!document.querySelector("[data-univention-design-system]")) {
  const i = document.createElement("style");
  i.setAttribute("data-univention-design-system", ""), i.textContent = qe, document.head.appendChild(i);
}
