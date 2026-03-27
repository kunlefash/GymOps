// ── Formspree Waitlist ──
const FORMSPREE_URL = 'https://formspree.io/f/xyknveqe';
const STORAGE_KEY = 'gymops_waitlist';

function getWaitlist() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  } catch {
    return [];
  }
}

function addToLocalWaitlist(email) {
  const list = getWaitlist();
  if (list.includes(email)) return false;
  list.push(email);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  return true;
}

// ── Form Handling ──
async function handleSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const input = form.querySelector('input[type="email"]');
  const btn = form.querySelector('button');
  const email = input.value.trim().toLowerCase();

  if (!email) return;

  const isNew = addToLocalWaitlist(email);
  const successEl = document.getElementById('waitlist-success');

  if (!isNew) {
    if (successEl) {
      successEl.hidden = false;
      successEl.textContent = "You're already on the list! We'll reach out soon.";
    }
    input.value = '';
    return;
  }

  const originalText = btn.textContent;
  btn.innerHTML = '<span>Sending...</span>';
  btn.disabled = true;

  try {
    const res = await fetch(FORMSPREE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({
        email: email,
        _subject: 'New GymOps Waitlist Signup!',
      }),
    });

    if (res.ok) {
      if (successEl) {
        successEl.hidden = false;
        successEl.textContent = "You're on the list! We'll be in touch soon.";
        successEl.style.borderColor = '';
        successEl.style.background = '';
        successEl.style.color = '';
      }
      btn.innerHTML = '<span>Added!</span>';
      btn.style.background = '#22c55e';
    } else {
      if (successEl) {
        successEl.hidden = false;
        successEl.textContent = 'Something went wrong. Please try again.';
        successEl.style.borderColor = 'rgba(239, 68, 68, 0.2)';
        successEl.style.background = 'rgba(239, 68, 68, 0.08)';
        successEl.style.color = '#ef4444';
      }
      btn.innerHTML = '<span>Try Again</span>';
    }
  } catch {
    if (successEl) {
      successEl.hidden = false;
      successEl.textContent = 'Network error. Please try again.';
      successEl.style.borderColor = 'rgba(239, 68, 68, 0.2)';
      successEl.style.background = 'rgba(239, 68, 68, 0.08)';
      successEl.style.color = '#ef4444';
    }
    btn.innerHTML = '<span>Try Again</span>';
  }

  input.value = '';
  btn.disabled = false;

  setTimeout(() => {
    btn.textContent = originalText;
    btn.style.background = '';
  }, 2500);
}

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
  const heroForm = document.getElementById('hero-form');
  const waitlistForm = document.getElementById('waitlist-form');

  if (heroForm) heroForm.addEventListener('submit', handleSubmit);
  if (waitlistForm) waitlistForm.addEventListener('submit', handleSubmit);

  // Scroll reveal animations
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        }
      });
    },
    { threshold: 0.1 }
  );

  document.querySelectorAll(
    '.bento-card, .step, .problem-grid, .cta-card, .section-header, .trust, .hero-visual'
  ).forEach((el) => {
    el.classList.add('fade-in');
    observer.observe(el);
  });

  // Parallax on dashboard preview (subtle mouse tracking)
  const dashPreview = document.querySelector('.dashboard-preview');
  if (dashPreview && window.innerWidth > 900) {
    document.addEventListener('mousemove', (e) => {
      const x = (e.clientX / window.innerWidth - 0.5) * 8;
      const y = (e.clientY / window.innerHeight - 0.5) * 8;
      dashPreview.style.transform = `perspective(1000px) rotateY(${x}deg) rotateX(${-y}deg)`;
    });
  }
});
