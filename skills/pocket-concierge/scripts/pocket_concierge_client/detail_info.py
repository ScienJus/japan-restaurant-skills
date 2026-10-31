"""Published terms and FAQ evidence; no on-site payment or age inference."""
import re


def practical_info(venue, url):
    evidence = []
    terms = venue.get('reservationTerms')
    if isinstance(terms, str):
        for paragraph in re.split(r'\r?\n\s*\r?\n', terms):
            if paragraph.strip():
                evidence.append({'field': 'reservationTerms', 'text': paragraph.strip(), 'source_url': url})
    for index, item in enumerate(venue.get('frequentlyAskedQuestions') or []):
        if not isinstance(item, dict):
            continue
        question, answer = item.get('question'), item.get('answer')
        if isinstance(question, str) and isinstance(answer, str):
            evidence.append({'field': f'frequentlyAskedQuestions[{index}]', 'text': question+'\n'+answer, 'source_url': url})
    reservation = [item for item in evidence if item['field'] == 'reservationTerms' or re.search(r'予約|reserv|booking', item['text'], re.I)]
    payment = [item for item in evidence if re.search(r'現金|カード|支払|決済|電子マネー|cash\b|credit|payment|paypay', item['text'], re.I)]
    children = [item for item in evidence if re.search(r'お子|子供|子ども|乳児|幼児|未就学|小学生|child(?:ren)?|infants?|bab(?:y|ies)|kids?', item['text'], re.I)]
    return {'reservation': {'accepted': None, 'required': None, 'evidence': reservation, 'availability_checked': False},
            'payment': {'cash_only': None, 'credit_cards_accepted': None, 'electronic_money_accepted': None,
                        'qr_payments_accepted': None, 'evidence': payment},
            'children': {'evidence': children, 'eligibility_checked': False},
            'links': [{'kind': 'booking_entry', 'platform': 'pocket_concierge', 'url': url, 'source_url': url,
                       'field': 'venue.id', 'verification': 'platform_listing'}]}
