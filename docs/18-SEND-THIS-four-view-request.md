<!-- Копирай блока по-долу и го прати на ChatGPT ЗАЕДНО с ref-05-986-futuristic-v3-CHOSEN.png -->

# Какво искаме и защо точно това

Имаме силует, който съвпада с `ref-05` до **3 mm отпред** — но само в един изглед. Страничният
изглед не носи нищо за **плана** и за **сеченията**, а именно там формите се разминават.

Четирите ортогонални изгледа дават калибровка **във всеки от тях поотделно**, защото във всеки има
колела, а следата (1465 / 1528 mm) и междуосието (2415 mm) са публикувани от workshop manual-а.
Оттам същата машинария, която мери страничния силует, ще мери формата в трите оси.

**Защо НЕ рендъри на отделни панели:** всяка генерация измисля каквото не вижда, тоест дванайсет
рендъра на панели са дванайсет различни коли. И панел сам по себе си не дава на калибровката за
какво да се хване — един калник няма междуосие в себе си.

**Числа не са нужни.** Всяко число в AI инфографика се игнорира по правило на проекта — размерите
идват от донора и от нашата спецификация. Искаме само формата.

---

## ПРОМПТ ЗА CHAT GPT (копирай оттук надолу, на английски — image моделите го следват по-точно)

```
Attached is the approved design for my one-off sports car (STATEV 001). I need a technical
four-view orthographic set OF THIS EXACT CAR, to use as a modelling reference in Blender.

Produce FOUR separate images, one per view:
  1. SIDE      — true left-side elevation
  2. FRONT     — true front elevation
  3. REAR      — true rear elevation
  4. TOP       — true plan view from directly above

HARD REQUIREMENTS — these make the images measurable, and without them they are unusable:

• TRUE ORTHOGRAPHIC PROJECTION. No perspective, no vanishing points, no lens distortion.
  The camera must be exactly on the axis for each view — dead level for side/front/rear,
  dead vertical for the top view.

• THE SAME CAR IN ALL FOUR. Same proportions, same surfaces, same details, same dark metallic
  green paint, same bronze wheels. This is one car photographed four times, not four designs.

• WHEELS FULLY VISIBLE, and bronze as in the attached image. Side view: both wheels, complete,
  not cropped. Front view: both front wheels. Rear view: both rear wheels. Top view: all four.
  The wheels are what I calibrate the scale from, so they must be sharp and unobstructed.

• CAR LEVEL AND STATIC. All four wheels on the ground, no rake, no motion blur, wheels
  straight ahead, roof/soft-top DOWN (open), doors and panels closed.

• PLAIN EVEN BACKGROUND. A single flat studio backdrop, clearly separated in brightness from
  the car. No floor reflections under the car, no props, no environment, no strong vignette.

• NOTHING OVERLAID. No text, no labels, no callouts, no dimension lines, no arrows, no logos,
  no watermarks, no grid. A clean image only.

• WHOLE CAR IN FRAME with a margin of roughly 10% on every side. High resolution.

• ONE VIEW PER IMAGE. Do not combine them into a collage.

Do not add any numbers or measurements — I will not use them; the dimensions come from the
donor chassis. I need the SHAPE only.

If you can also produce three close-ups OF THE SAME CAR, they would help a lot:
  A. the side air intake ahead of the rear wheel, seen straight on from the side
  B. the front mask and light blade, seen straight on from the front
  C. the rear structure over the diffuser, seen straight on from the rear
```

---

## Какво ще направя с тях

1. Калибрирам всеки изглед по колелата — както страничният вече е калибриран на 2.8753 mm/px,
   потвърдено от основата на стъклото, която излезе 969 срещу публикуваните донорски 970.
2. Рендирам модела от нагласена камера за всеки изглед и сравнявам контурите станция по станция.
3. Давам отклонение в милиметри **по трите оси**, а не по една — планът е най-голямата сляпа зона.
4. Първата проверка, която ще пусна, е дали четирите изгледа са една и съща кола: съотношенията
   междуосие-към-дължина и следа-към-ширина трябва да съвпадат между изгледите. Ако не съвпадат,
   казвам го и искаме комплекта наново, вместо да меря срещу четири различни коли.
