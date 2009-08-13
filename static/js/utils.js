function setSlug(title_id, slug_id) {
    slug = document.getElementById(title_id).value;

    slug = slug.replace(/^\s+|\s+$/g, ''); // trim
    slug = slug.replace(/[^a-zA-Z0-9 -]/g, ''); // remove invalid chars
    slug = slug.replace(/\s+/g, '-'); // collapse whitespace and replace by -

    document.getElementById(slug_id).value = slug.toLowerCase();
}
