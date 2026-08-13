import json
import re
from io import BytesIO

import docx2txt
from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_tenants.utils import schema_context

from orgs.models import Customer, Post

User = get_user_model()

# ==========================================
# 1. HEADLESS WORD DOCUMENT (.DOCX) PARSER
# ==========================================

# file: orgs/document_processor.py





def extract_text_from_docx(text_file_field):
    """Safely extracts text using Django Storage layer."""
    try:
        with default_storage.open(text_file_field.name, 'rb') as f:
            docx_bytes = BytesIO(f.read())
            text = docx2txt.process(docx_bytes)
            return text
    except Exception as e:
        print(f"[Parser Error] Failed reading file from storage context: {e}")
        return ""


def text_to_html_paragraphs(text):
    """Converts structured text segments into uniform clean HTML paragraph blocks."""
    if not text:
        return ""
    text = re.sub(r'\n\s*\n', '\n', text)
    lines = text.split('\n')
    return ''.join(f'<p>{line.strip()}</p>\n' for line in lines if line.strip())


def process_html_content(post, html_paragraphs, language='pt'):
    """Parses paragraphs to inject clean components for Next.js (Tailwind classes)."""
    soup = BeautifulSoup(html_paragraphs, 'html.parser')
    paragraphs = soup.find_all('p')
    new_elements = []
    
    # Tailwind classes por idioma (opcional)
    text_classes = {
        'pt': 'text-base md:text-lg text-slate-700 leading-relaxed mb-4',
        'en': 'text-base md:text-lg text-slate-700 leading-relaxed mb-4',
        'fr': 'text-base md:text-lg text-slate-700 leading-relaxed mb-4',
    }
    
    for p in paragraphs:
        text_content = p.get_text().strip()
        if not text_content:
            continue
            
        # Matches external static cloud image URLs
        if text_content.startswith("https://") and any(ext in text_content.lower() for ext in ['.jpg', '.png', '.jpeg', '.gif']):
            img_tag = soup.new_tag("img", attrs={
                "class": "w-full rounded-xl my-6 object-cover aspect-video shadow-md dynamic-doc-img",
                "src": text_content,
                "alt": f"{post.title} - {language}"
            })
            new_elements.append(str(img_tag))
            
        # Matches YouTube streaming media URLs
        elif "youtube.com" in text_content or "youtu.be" in text_content:
            video_id = text_content.split('v=')[-1] if 'v=' in text_content else text_content.split('/')[-1]
            video_id = video_id.split('&')[0]
            embed_url = f"https://www.youtube.com/embed/{video_id}"
            
            wrapper = soup.new_tag("div", attrs={"class": "aspect-video w-full my-6 rounded-xl overflow-hidden shadow-lg"})
            iframe = soup.new_tag("iframe", attrs={
                "src": f"{embed_url}?rel=0",
                "class": "w-full h-full",
                "allowfullscreen": "true",
                "title": "YouTube Video Player"
            })
            wrapper.append(iframe)
            new_elements.append(str(wrapper))
            
        # Standard descriptive textual paragraphs
        else:
            p['class'] = text_classes.get(language, text_classes['pt'])
            new_elements.append(str(p))
            
    return ''.join(new_elements)


def process_document_for_language(post, language, text_field_name, processed_field_name):
    """
    Process a document for a specific language.
    
    Args:
        post: Post instance
        language: Language code ('pt', 'en', 'fr')
        text_field_name: Name of the field containing the text file
        processed_field_name: Name of the field to store the processed JSON
    """
    text_file = getattr(post, text_field_name)
    if not text_file:
        return None
        
    try:
        # Extract text from DOCX
        extracted_text = extract_text_from_docx(text_file)
        if not extracted_text:
            return None
            
        # Create excerpt
        clean_single_line = extracted_text.replace('\n', ' ').strip()
        excerpt = (clean_single_line[:97] + "...") if len(clean_single_line) > 97 else clean_single_line
        
        # Convert to HTML
        html_raw = text_to_html_paragraphs(extracted_text)
        processed_html = process_html_content(post, html_raw, language)
        
        # Update the translated fields
        desc_attr = f"description_{language}"
        text_attr = f"text_{language}"
        
        if hasattr(post, desc_attr) and hasattr(post, text_attr):
            if not getattr(post, desc_attr):
                setattr(post, desc_attr, excerpt)
            setattr(post, text_attr, processed_html)
        else:
            # Fallback for non-translated fields
            if language == 'pt' and not post.description:
                post.description = excerpt
            if language == 'pt' and not post.text:
                post.text = processed_html

        # Create JSON payload
        payload = {
            "meta_excerpt": excerpt,
            "language": language,
            "html_content": processed_html,
            "post_title": post.title,
            "post_id": post.id,
        }
        
        # Save JSON file
        file_name = f"processed_{post.slug or 'post'}_{post.id}_{language}.json"
        file_path = f"cms/posts/processed/{language}/{file_name}"
        
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
            
        file_content = json.dumps(payload, ensure_ascii=False, indent=2)
        saved_path = default_storage.save(file_path, ContentFile(file_content.encode('utf-8')))
        
        # Update the processed file field
        setattr(post, processed_field_name, saved_path)
        
        return saved_path
        
    except Exception as e:
        print(f"[Parser Error] Failed processing document for {language}: {e}")
        return None


@receiver(post_save, sender=Post)
def process_post_documents(sender, instance, created, **kwargs):
    """Intercepts save signals to parse documents for each language."""
    # Prevent recursive loops
    if hasattr(instance, '_processing_docx') and instance._processing_docx:
        return

    instance._processing_docx = True
    
    # Process each language
    language_configs = [
        ('pt', 'text_file_pt', 'processed_text_file_pt'),
        ('en', 'text_file_en', 'processed_text_file_en'),
        ('fr', 'text_file_fr', 'processed_text_file_fr'),
    ]
    
    processed_any = False
    for language, text_field, processed_field in language_configs:
        text_file = getattr(instance, text_field)
        if text_file:
            print(f"[Document Pipeline] Processing {language} document for: {instance.title}")
            processed_path = process_document_for_language(
                instance, language, text_field, processed_field
            )
            if processed_path:
                processed_any = True
    
    # Also process legacy field if present
    if instance.text_file:
        print(f"[Document Pipeline] Processing legacy document for: {instance.title}")
        # Determine language from filename or use default
        language = 'pt'  # default
        if '_en_' in instance.text_file.name:
            language = 'en'
        elif '_fr_' in instance.text_file.name:
            language = 'fr'
        
        processed_path = process_document_for_language(
            instance, language, 'text_file', 'processed_text_file'
        )
        if processed_path:
            processed_any = True
    
    # Save if any changes were made
    if processed_any:
        instance.save(update_fields=[
            'description_pt', 'text_pt', 'processed_text_file_pt',
            'description_en', 'text_en', 'processed_text_file_en',
            'description_fr', 'text_fr', 'processed_text_file_fr',
            'processed_text_file', 'description', 'text'
        ])
    
    del instance._processing_docx

# ==========================================
# 2. CROSS-SCHEMA USER/CUSTOMER SYNC PIPELINE
# ==========================================

@receiver(
    post_save,
    sender=User,
    dispatch_uid="create_customer_profile_on_new_user"
)
def create_customer_profile_on_new_user(sender, instance, created, **kwargs):
    """
    Listens to User creation events and delegates profile provisioning 
    safely on successful database transaction commits.
    """
    if not created or not instance.is_customer:
        return

    tenant = getattr(instance, "tenant", None)
    print(tenant)
    if tenant and tenant.schema_name != "public":
        # Wraps execution to trigger strictly *after* the global transaction clears successfully
        transaction.on_commit(
            lambda: create_profile_in_tenant_schema(tenant.schema_name, instance.id)
        )


def create_profile_in_tenant_schema(schema_name, user_id):
    """Executes safe record provisioning isolated inside the target tenant schema footprint."""
    with schema_context(schema_name):
        try:
            # Re-fetches the user instance safely inside the active schema scope context
            user_instance = User.objects.get(id=user_id)
            Customer.objects.get_or_create(user=user_instance)
            print(f"[Sync Success] Customer profile generated for User ID {user_id} inside schema '{schema_name}'.")
        except User.DoesNotExist:
            print(f"[Sync Error] User ID {user_id} was missing when executing profile creation inside '{schema_name}'.")
