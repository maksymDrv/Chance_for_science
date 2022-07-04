from django.utils.datastructures import MultiValueDict
from django.http.request import QueryDict
from django.http import HttpRequest
from django.shortcuts import render
from . import models

def form(request: HttpRequest):
    if request.method == "POST":
        post: QueryDict = request.POST
        files: MultiValueDict = request.FILES

        check_title = lambda title: title if not title == 'Choose a value' else ''
        check_others = lambda current, other: post[other] if current == 'other' else current
        check_checkbox = lambda check, file: post[file] if not check == 'none' else None
        check_file = lambda check, data_name: files[data_name] if not check == 'none' and file_exist(files, data_name) else None
        check_image = lambda check, data_name: files[data_name] if check == '1' and file_exist(files, data_name) else None
        check_access = lambda abstract, cv, check: 1 if abstract and cv and check == '1' else 0

        academic_title = check_title(post['form4title[]'])

        title = f"{post['form4given-name']} {post['form4family-name']}"
        if academic_title:
            title = f"{academic_title} {post['form4given-name']} {post['form4family-name']}"

        announce = post.get('form4announce')
        abstract = check_checkbox(post['form4abstract-enter'], 'form4abstract')
        cv = check_checkbox(post['form4short-cv-enter'], 'form4short-cv')
        image = check_image(announce, 'form4portrait-upload')

        data = models.Content(
            academic_title      = academic_title,
            given_name          = post['form4given-name'],
            family_name         = post['form4family-name'],
            gender              = post['form4gender[]'],
            email               = post['form4email'],
            telephone           = post['form4telephone'],
            academic_status     = check_others(post['form4academic-status[]'], 'form4academic-status-other'),
            country_origin      = check_others(post['form4country-origin[]'], 'form4origin-other'),
            current_location    = check_others(post['form4current-location[]'], 'form4current-location-other'),
            profession          = post.getlist('form4profession[]'),
            university          = post['form4university'],
            type_participation  = post['form4participation-type'],
            presentation_title  = post['form4presentation-title'],
            abstract            = abstract,
            short_cv            = cv,
            presentation_upload = check_file(post['form4presentation-upload-option'], 'form4presentation-upload'),
            portrait            = image
        )
        data.save()

        img = '{"image_intro":"images\/Profil.png","float_intro":"","image_intro_alt":"' + title \
                + '","image_intro_caption":"","image_fulltext":"images\/Profil.png","float_fulltext":"","image_fulltext_alt":"' \
                + title + '","image_fulltext_caption":""}'

        if data.portrait:
            url = f'http://h2976860.stratoserver.net{data.portrait.url}'
            img = '{"image_intro":"' + url + '","float_intro":"","image_intro_alt":"' + title \
                + '","image_intro_caption":"","image_fulltext":"' + url + '","float_fulltext":"","image_fulltext_alt":"' \
                + title + '","image_fulltext_caption":""}'

        access = check_access(abstract, cv, announce)

        core_id = models.ConfContentitemTagMap.objects.latest('core_content_id').core_content_id + 1

        data = models.ConfContent(
            title   = title,
            introtext = abstract,
            fulltext = cv,
            images  = img,
            access  = access
        )
        data.save()

        tags = post.getlist('form4profession[]')

        for tag in post.get('form4other-profession').split('|'):
            if tag:
                new_tag = models.ConfTags.objects.filter(title=tag).exists()
                if not new_tag:
                    low_tag = tag.replace(' ', '-').lower()
                    last_rgt = models.ConfTags.objects.latest('rgt').rgt + 1
                    new_tag = models.ConfTags(
                        lft = last_rgt,
                        rgt = last_rgt + 1,
                        title = tag,
                        path = low_tag,
                        alias = low_tag
                    )
                    new_tag.save()
                else: 
                    new_tag = models.ConfTags.objects.filter(title=tag)[0]
                tags.append(new_tag.id)

        for tag in tags:
            models.ConfContentitemTagMap(
                core_content_id = core_id,
                content_item_id = data.id,
                tag_id = tag
            ).save()
        
        return render(request, 'thank.html', {
            'title': title
        })

    return render(request, 'form.html', 
        {
            'professions': models.ConfTags.objects.all()
        })

def file_exist(files: MultiValueDict, key: str):
    for current_key in files.keys():
        if current_key == key:
            return True
    return False