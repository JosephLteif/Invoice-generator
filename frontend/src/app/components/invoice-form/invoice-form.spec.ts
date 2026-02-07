import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InvoiceForm } from './invoice-form';

describe('InvoiceForm', () => {
  let component: InvoiceForm;
  let fixture: ComponentFixture<InvoiceForm>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InvoiceForm]
    })
    .compileComponents();

    fixture = TestBed.createComponent(InvoiceForm);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
